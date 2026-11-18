"""SSH remote execution environment with ControlMaster connection persistence."""

import contextlib
import hashlib
import logging
import os
import posixpath
import shlex
import shutil
import stat
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Iterable

from hermes_constants import socket_safe_tmpdir
from tools.environments.base import BaseEnvironment, EnvironmentConnectionError
from tools.environments.base_output import _popen_bash
from tools.environments.file_sync import (
    FileSyncManager, iter_sync_files, quoted_mkdir_command, quoted_rm_command, unique_parent_dirs)
from tools.environments.local import build_subprocess_env
from tools.environments.remote_common import (
    bash_argv, client_env_with, load_hermes_env_vars, prepend_unset, resolve_passthrough_env, run_capture)
from tools.spill_safety import ensure_owned_private_dir

logger = logging.getLogger(__name__)

# Windows OpenSSH has no Unix-socket ControlMaster: ControlPath/ControlMaster options
# fail the connection outright ('getsockname failed: Not a socket'). Skip multiplexing there.
# Skip multiplexing there; each command pays a fresh connection but the backend works. See #73927.
_SSH_MULTIPLEX = os.name != "nt"

# Module-level binding: tests patch ``ssh._load_hermes_env_vars`` to fake the .env file.
_load_hermes_env_vars = load_hermes_env_vars


def _ensure_ssh_available() -> None:
    """Fail fast with a clear error when the SSH client is unavailable."""
    for tool in ("ssh", "scp"):
        if not shutil.which(tool):
            raise RuntimeError(f"{tool.upper()} is not installed or not in PATH. "
                               "Install OpenSSH client: apt install openssh-client")


def _sync_error(reason: str, subject: str, what: str = "the SSH connection") -> EnvironmentConnectionError:
    return EnvironmentConnectionError(
        reason, retry_hint=f"{subject} failed — verify {what} is healthy, then retry.")


# A control dir must leave room for ``/<16 hex>.sock`` plus the 17-byte suffix OpenSSH appends to
# its temporary ControlMaster listener, inside macOS's 103 usable ``sun_path`` bytes (Linux: 107).
_CONTROL_DIR_MAX_BYTES = 103 - len("/0123456789abcdef.sock") - 17
_SHORT_TMP_ROOT = "/tmp"  # no-tmp: ok — AF_UNIX sun_path budget; every dir under it is ownership-checked


def _is_private_runtime_dir(path: str) -> bool:
    """``$XDG_RUNTIME_DIR`` as the spec promises it (a real dir we own, no group/other access), the same
    test the gateway's control socket applies: an inherited or mis-set value naming a shared dir must
    not host a ``hermes-ssh`` leaf another user could create first."""
    try:
        # Path drops trailing / and /. before lstat (which would otherwise follow a symlink),
        # while retaining .. components so lstat checks the actual traversed directory.
        st = Path(path).lstat()
    except OSError:
        return False
    return stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid() and not st.st_mode & 0o077  # windows-footgun: ok — POSIX only (_SSH_MULTIPLEX)


def _open_control_dir() -> tuple[Path, bool]:
    """Per-user ControlMaster socket dir that fits ``sun_path`` (#133436) and is proven ours (#80284).

    Candidates, best first: ``$XDG_RUNTIME_DIR`` (per-user 0700), then a per-uid name under the
    socket-safe temp root and under ``/tmp`` (a deep profile scratch TMPDIR does not fit). Those
    names are predictable and the roots may be shared, so a candidate that is not a real directory
    we own (pre-created by another user, or a planted symlink) is refused rather than adopted;
    when every one is squatted, a fresh ``mkdtemp`` dir keeps the backend up. The flag is True
    only for that fallback: it belongs to this instance alone and goes when the instance does."""
    if not _SSH_MULTIPLEX:  # no Unix-socket ControlMaster; %TEMP% is per-user
        return Path(ensure_owned_private_dir(Path(tempfile.gettempdir()) / "hermes-ssh")), False
    per_user = f"hermes-ssh-{os.getuid()}"  # windows-footgun: ok — POSIX only (_SSH_MULTIPLEX)
    roots = list(dict.fromkeys(r for r in (socket_safe_tmpdir(), _SHORT_TMP_ROOT) if os.path.isdir(r)))
    candidates = [Path(root) / per_user for root in roots]
    xdg = os.environ.get("XDG_RUNTIME_DIR", "")
    if os.path.isabs(xdg) and _is_private_runtime_dir(xdg):
        candidates.insert(0, Path(xdg) / "hermes-ssh")
    for candidate in candidates:
        if len(os.fsencode(candidate)) > _CONTROL_DIR_MAX_BYTES:
            continue
        try:
            return Path(ensure_owned_private_dir(candidate)), False
        except OSError as exc:
            logger.warning("SSH: not using control-socket dir %s: %s", candidate, exc)
    return Path(tempfile.mkdtemp(prefix="hssh-", dir=min(roots, key=len))), True


def _parse_remote_hashes(output: bytes, base: str) -> dict[str, str]:
    """``<sha256>  ./<path>`` lines -> ``{base/path: sha256}``. Escaped names (a leading ``\\``
    marks a backslash or newline in the name) and anything unparsable are skipped: such a
    file simply gets uploaded."""
    hashes = {}
    for line in output.decode(errors="surrogateescape").splitlines():
        digest, sep, name = line.partition("  ")
        if not sep:
            digest, sep, name = line.partition(" *")  # shasum/sha256sum binary-mode marker
        if (not sep or len(digest) != 64 or not name.startswith("./")
                or any(c not in "0123456789abcdef" for c in digest)):
            continue
        hashes[f"{base}/{name[2:]}"] = digest
    return hashes


def _remote_sync_relative_path(remote_path: str, base: str) -> str:
    """Return a safe POSIX archive member path beneath the remote sync base."""
    try:
        relative = posixpath.relpath(remote_path, base)
    except ValueError as exc:
        raise RuntimeError(f"remote path {remote_path!r} is not under sync base {base!r}") from exc
    if relative in {".", ".."} or relative.startswith("../"):
        raise RuntimeError(f"remote path {remote_path!r} escapes sync base {base!r}")
    return relative


def _local_sync_staging_path(staging: str, relative: str, *, path_module=None) -> str:
    """Map a POSIX archive member beneath a host staging directory."""
    paths = path_module or os.path
    if paths.sep == "\\":
        reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                    *(f"LPT{i}" for i in range(1, 10))}
        for component in relative.split("/"):
            stem = component.split(".", 1)[0].upper()
            invalid = (
                not component
                or component.endswith((".", " "))
                or any(ord(char) < 32 or char in '<>:"\\|?*' for char in component)
                or stem in reserved
            )
            if invalid:
                raise RuntimeError(
                    f"remote archive path {relative!r} is not representable on Windows"
                )
    root = paths.abspath(staging)
    staged = paths.abspath(paths.join(root, *relative.split("/")))
    try:
        contained = paths.commonpath((root, staged)) == root
    except ValueError:
        contained = False
    if not contained:
        raise RuntimeError(f"remote archive path {relative!r} escapes staging directory")
    return staged


class SSHEnvironment(BaseEnvironment):
    """Run commands on a remote machine over SSH.

    Spawn-per-call: every execute() spawns a fresh ``ssh ... bash -c`` process.
    Session snapshot preserves exported env vars across calls (unless
    ``persistent=False``); CWD persists via in-band
    stdout markers. Uses SSH ControlMaster for connection reuse.
    """

    # Passthrough values are re-forwarded on every command (see _run_bash), so like docker/local
    # they stay out of the remote snapshot under multiplex.
    _profile_scoped_passthrough = True
    _passwordless_sudo_probe_supported = True
    # cleanup() only closes the ControlMaster sockets: a nohup'd background job keeps running on
    # the host and the next execute() reconnects, so its poller still collects the real exit.
    cleanup_stops_processes = False

    def __init__(self, host: str, user: str, cwd: str = "~",
                 timeout: int = 60, port: int = 22, key_path: str = "",
                 probe_only: bool = False, sync_files: bool = True, persistent: bool = True):
        from tools.terminal_tool_config import coerce_ssh_remote_cwd

        # cwd may be a raw terminal.cwd naming a directory on the machine running Hermes; coercion is
        # idempotent, so callers that already coerced are unaffected.
        super().__init__(cwd=coerce_ssh_remote_cwd(cwd, "ssh"), timeout=timeout, persist_env=persistent)
        self.host, self.user, self.port, self.key_path = host, user, port, key_path
        self.control_dir, self._owns_control_dir = _open_control_dir()
        # Short, deterministic socket name: the path must stay under macOS's 104-byte sun_path
        # limit (raw user@host:port + SSH's 16-byte suffix under a deep $TMPDIR exceeds it), and
        # stability across reconnects keeps ControlMaster reuse working. A probe gets its own
        # per-instance socket so its cleanup() can never close the agent's shared master.
        socket_key = f"{user}@{host}:{port}"
        if probe_only:
            socket_key = f"{socket_key}:probe:{self._session_id}"
        _socket_id = hashlib.sha256(socket_key.encode()).hexdigest()[:16]
        self.control_socket = self.control_dir / f"{_socket_id}.sock"
        self._sync_manager = None  # cleanup() reads it; set before anything below can raise
        try:
            _ensure_ssh_available()
            self._establish_connection()
        except BaseException:
            if self._owns_control_dir:  # no instance survives to clean up this private fallback
                shutil.rmtree(self.control_dir, ignore_errors=True)
            raise
        if probe_only:
            return
        self._remote_home_detected = False
        self._remote_gzip = False  # set by the first remote hash listing
        self._remote_home = self._detect_remote_home()
        if sync_files:
            self._ensure_remote_dirs()
            self._sync_manager = FileSyncManager(
                get_files_fn=lambda: iter_sync_files(f"{self._remote_home}/.hermes"),
                upload_fn=self._scp_upload, delete_fn=self._ssh_delete,
                bulk_upload_fn=self._ssh_bulk_upload, bulk_download_fn=self._ssh_bulk_download,
                upload_batch_max_files=256, upload_batch_max_bytes=16 * 1024 * 1024,
                remote_hashes_fn=self._ssh_remote_hashes)
            self._sync_manager.sync(force=True)
        self.init_session()

    def _control_socket_for(self, send_env: tuple[str, ...]) -> Path:
        """One ControlMaster per SendEnv name-set, beside the plain target socket: a mux master only
        relays the env names it was itself started with and silently drops the rest, so a passthrough
        command must ride a master that knows its names. scp/sync/probes keep the plain socket."""
        plain = Path(self.control_socket)
        if not send_env:
            return plain
        # <target-id[:8]><names-hash[:8]>.sock: same length as the plain socket (macOS's 104-byte
        # sun_path cap) and prefix-globbable so cleanup() finds every sibling without extra state.
        digest = hashlib.sha256(" ".join(send_env).encode()).hexdigest()[:8]
        return plain.with_name(f"{plain.stem[:8]}{digest}.sock")

    def _control_sockets(self) -> list[Path]:
        """The plain socket plus every SendEnv-set sibling (shared 8-char target prefix)."""
        plain = Path(self.control_socket)
        siblings = sorted(plain.parent.glob(f"{plain.stem[:8]}*.sock")) if plain.parent.is_dir() else []
        return [plain, *(s for s in siblings if s != plain)]

    def _target_flags(self, port_flag: str) -> list:
        """Port/key flags shared by ssh (``-p``) and scp (``-P``)."""
        flags = [port_flag, str(self.port)] if self.port != 22 else []
        return flags + (["-i", self.key_path] if self.key_path else [])

    def _build_ssh_command(self, extra_args: list | None = None, send_env: Iterable[str] = ()) -> list:
        send_env = tuple(sorted(send_env))
        cmd = ["ssh"]
        if _SSH_MULTIPLEX:
            cmd.extend(["-o", f"ControlPath={self._control_socket_for(send_env)}",
                        "-o", "ControlMaster=auto", "-o", "ControlPersist=300"])
        cmd.extend(["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10"])
        # Without keepalives a stalled link hangs every mux client until its own timeout;
        # these match the gateway SSH transport (gateway_connections_ssh_transport.py).
        cmd.extend(["-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3"])
        # Names only; values ride the ssh client's own environment (never the remote command text).
        cmd.extend(arg for name in send_env for arg in ("-o", f"SendEnv={name}"))
        cmd.extend(self._target_flags("-p"))
        cmd.extend(extra_args or [])
        cmd.append(f"{self.user}@{self.host}")
        return cmd

    def _run_ssh(self, remote_cmd: str, timeout: float) -> subprocess.CompletedProcess:
        """Run one remote shell command over the multiplexed connection, capturing output."""
        return run_capture(self._build_ssh_command() + [remote_cmd], timeout=timeout)

    def _run_ssh_checked(self, remote_cmd: str, timeout: float, reason: str, subject: str) -> None:
        result = self._run_ssh(remote_cmd, timeout=timeout)
        if result.returncode != 0:
            raise _sync_error(f"{reason}: {result.stderr.strip()}", subject)

    def _establish_connection(self):
        try:
            result = self._run_ssh("echo 'SSH connection established'", timeout=15)
        except subprocess.TimeoutExpired:
            raise EnvironmentConnectionError(
                f"SSH connection to {self.user}@{self.host} timed out",
                retry_hint=(f"Check that {self.host} is up and reachable on port {self.port} "
                            "and that sshd is running, then retry."))
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise EnvironmentConnectionError(
                f"SSH connection failed: {error_msg}",
                retry_hint=(f"Check that {self.host} is up, sshd is running on port {self.port}, and "
                            f"{self.user} can log in with the configured key, then retry — "
                            "the connection is re-established automatically."))

    def _detect_remote_home(self) -> str:
        """Detect the remote user's home directory."""
        with contextlib.suppress(Exception):
            result = self._run_ssh("echo $HOME", timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                logger.debug("SSH: remote home = %s", result.stdout.strip())
                self._remote_home_detected = True
                return result.stdout.strip()
        return "/root" if self.user == "root" else f"/home/{self.user}"

    def _ensure_remote_dirs(self) -> None:
        """Create base ~/.hermes directory tree on remote in one SSH call."""
        base = f"{self._remote_home}/.hermes"
        self._run_ssh(quoted_mkdir_command([base, f"{base}/skills", f"{base}/credentials", f"{base}/cache"]),
                      timeout=10)

    def _scp_upload(self, host_path: str, remote_path: str) -> None:
        """Upload a single file via scp over ControlMaster."""
        self._run_ssh(f"mkdir -p {shlex.quote(str(Path(remote_path).parent))}", timeout=10)
        scp_cmd = ["scp"] + (["-o", f"ControlPath={self.control_socket}"] if _SSH_MULTIPLEX else [])
        scp_cmd += self._target_flags("-P") + [host_path, f"{self.user}@{self.host}:{remote_path}"]
        result = run_capture(scp_cmd, timeout=30)
        if result.returncode != 0:
            raise _sync_error(f"scp failed: {result.stderr.strip()}", f"File sync to {self.user}@{self.host}")

    def _ssh_bulk_upload(self, files: list[tuple[str, str]]) -> None:
        """Upload many files in one tar-over-SSH stream: local ``tar c`` piped through one SSH
        connection to remote ``tar x``, after a single batched ``mkdir -p``."""
        if not files:
            return
        base = f"{self._remote_home}/.hermes"
        validated_files = []
        for host_path, remote_path in files:
            relative = _remote_sync_relative_path(remote_path, base)
            validated_files.append((host_path, posixpath.join(base, relative), relative))

        upload_bytes = sum(os.path.getsize(host) for host, _ in files)
        gzip = getattr(self, "_remote_gzip", False)  # unproven (no listing yet) -> uncompressed
        # Symlink staging avoids fragile GNU tar --transform rules. Archive
        # only explicit file entries instead of the staging root, otherwise
        # remote tar sees parent directory headers like `.` and may fail while
        # trying to restore metadata on restricted systems such as TrueNAS.
        # On Windows without Developer Mode, symlink creation raises OSError
        # with winerror 1314 (privilege not held). Only that case falls back to
        # a plain copy; all other OSErrors re-raise.
        with (
            tempfile.TemporaryDirectory(prefix="hermes-ssh-bulk-") as staging,
            tempfile.TemporaryDirectory(prefix="hermes-ssh-manifest-") as manifest_dir,
        ):
            tar_entries: list[str] = []
            for host_path, _, rel_remote in validated_files:
                staged = _local_sync_staging_path(staging, rel_remote)
                os.makedirs(os.path.dirname(staged), exist_ok=True)
                try:
                    os.symlink(os.path.abspath(host_path), staged)
                except OSError as e:
                    if getattr(e, "winerror", None) != 1314:
                        raise
                    shutil.copy2(host_path, staged)
                tar_entries.append(rel_remote)

            parents = unique_parent_dirs([
                (host_path, remote_path)
                for host_path, remote_path, _ in validated_files
            ])
            if parents:
                self._run_ssh_checked(quoted_mkdir_command(parents), 30, "remote mkdir failed",
                                      f"Remote directory setup on {self.host}")

            # Keep control data outside the payload: a same-named staged symlink
            # must never be followed when opening the manifest for writing.
            manifest_path = os.path.join(manifest_dir, "entries")
            with open(manifest_path, "wb") as manifest:
                manifest.writelines(os.fsencode(entry) + b"\0" for entry in tar_entries)

            tar_cmd = [
                "tar", "--no-xattrs", "-czhf" if gzip else "-chf", "-",
                "-C", staging, "--null", "-T", manifest_path,
            ]
            ssh_cmd = self._build_ssh_command()
            # The archive contains explicit file entries only, so portable
            # extraction cannot overwrite metadata of existing parent dirs. gzip (only once the
            # listing proved the remote has it): the support tree is mostly text, and a mux client
            # cannot enable ssh -C on an existing master.
            ssh_cmd.append(f"tar x{'z' if gzip else ''}f - -C {shlex.quote(base)}")

            # Preserve the caller's environment for the local tar process while
            # routing through the shared spawn-env guard. SSH sync may need
            # caller credentials/config, so this intentionally keeps secrets
            # and the real HOME; COPYFILE_DISABLE suppresses macOS metadata.
            tar_env = build_subprocess_env(
                scrub_secrets=False,
                inherit_profile_home=False,
                extra={"COPYFILE_DISABLE": "1"},
            )
            tar_proc = subprocess.Popen(
                tar_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=tar_env,
            )
            try:
                ssh_proc = subprocess.Popen(ssh_cmd, stdin=tar_proc.stdout,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception:
                tar_proc.kill()
                tar_proc.wait()
                raise
            tar_proc.stdout.close()  # let tar_proc receive SIGPIPE if ssh_proc exits early
            try:
                # Normal batches are small; a single oversized file cannot be split
                # by the manifest. Budget 256 KiB/s plus connection/extraction overhead
                # rather than retrying that file forever under a fixed 120 s deadline.
                _, ssh_stderr = ssh_proc.communicate(timeout=120 + upload_bytes / (256 * 1024))
                # communicate() (not wait()) drains stderr so tar can't deadlock on >PIPE_BUF errors.
                if tar_proc.poll() is None:
                    _, tar_stderr_raw = tar_proc.communicate(timeout=10)
                else:
                    tar_stderr_raw = tar_proc.stderr.read() if tar_proc.stderr else b""
            except subprocess.TimeoutExpired:
                for proc in (tar_proc, ssh_proc):
                    proc.kill()
                for proc in (tar_proc, ssh_proc):
                    proc.wait()  # kill both first, then reap: never wait on one while the other blocks
                raise EnvironmentConnectionError(
                    "SSH bulk upload timed out",
                    retry_hint=f"Bulk file sync to {self.host} timed out — check the connection and retry.")
            if tar_proc.returncode != 0:
                raise RuntimeError(f"tar create failed (rc={tar_proc.returncode}): "
                                   f"{tar_stderr_raw.decode(errors='replace').strip()}")
            if ssh_proc.returncode != 0:
                raise _sync_error(f"tar extract over SSH failed (rc={ssh_proc.returncode}): "
                                  f"{ssh_stderr.decode(errors='replace').strip()}",
                                  f"File sync over SSH to {self.host}", what="the connection")
        logger.debug("SSH: bulk-uploaded %d file(s) via tar pipe", len(files))

    @staticmethod
    def _remote_hash_script(base: str, roots: list[str]) -> str:
        """POSIX sh: ``HERMES_GZIP_OK`` when the remote can gunzip, then ``<sha256>  ./<path>`` for
        every regular file under the synced *roots* of *base* (GNU coreutils or macOS ``shasum``).
        Missing roots or a missing tree list nothing."""
        dirs = " ".join(shlex.quote(f"./{root}") for root in roots)
        probe = "command -v gzip >/dev/null 2>&1 && echo HERMES_GZIP_OK"
        if not roots:  # BSD find needs a path; GNU find would default to the whole tree
            return probe
        return (f"{probe}; cd {shlex.quote(base)} 2>/dev/null || exit 0; "
                "if command -v sha256sum >/dev/null 2>&1; then h=sha256sum; else h='shasum -a 256'; fi; "
                f"find {dirs} -type f ! -name '*.sock' -print0 2>/dev/null | xargs -0 $h")

    def _sync_roots(self) -> list[str]:
        """Top-level synced dirs (two levels under ``cache/``), so the listing skips remote
        sessions, logs and caches this host never pushes."""
        base = f"{self._remote_home}/.hermes"
        roots = set()
        for _, remote_path in iter_sync_files(base):
            if not remote_path.startswith(base + "/"):
                continue
            parts = remote_path[len(base) + 1:].split("/")
            depth = 2 if parts[0] == "cache" and len(parts) > 2 else 1
            if len(parts) > depth:
                roots.add("/".join(parts[:depth]))
        return sorted(roots)

    def _ssh_remote_hashes(self) -> dict[str, str]:
        """Hashes of the files the remote ``~/.hermes`` already holds, keyed like sync paths; also
        records whether uploads may be gzip-compressed."""
        base = f"{self._remote_home}/.hermes"
        roots = self._sync_roots()
        # sh -c: the remote login shell may be zsh, which does not word-split an unquoted $h.
        cmd = self._build_ssh_command() + [f"sh -c {shlex.quote(self._remote_hash_script(base, roots))}"]
        result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=30, check=False)
        if result.returncode == 255:  # ssh itself failed; xargs/find statuses still list the rest
            raise _sync_error(f"remote hash listing failed: {result.stderr.decode(errors='replace').strip()}",
                              f"File sync listing on {self.host}")
        self._remote_gzip = b"HERMES_GZIP_OK" in result.stdout.splitlines()
        return _parse_remote_hashes(result.stdout, base)

    def _ssh_bulk_download(self, dest: Path) -> None:
        """Download remote .hermes/ as a tar archive."""
        # Tar from / with the full path so archive entries keep absolute paths
        # (home/user/.hermes/skills/f.py), matching _pushed_hashes keys.
        rel_base = f"{self._remote_home}/.hermes".lstrip("/")
        # Live sockets inside .hermes (gateway.sock and friends) cannot be archived: tar prints
        # "socket ignored" and some builds exit 2, which failed every sync-back and left a
        # multi-GB temp tar behind on each retry. Exclude them up front.
        ssh_cmd = self._build_ssh_command() + [
            f"tar cf - --exclude='*.sock' -C / {shlex.quote(rel_base)}"]
        with open(dest, "wb") as f:
            result = subprocess.run(ssh_cmd, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.PIPE, timeout=120, check=False)
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace").strip()
            # A socket not named *.sock is the only rc=2 we knowingly accept, and only when
            # nothing else was reported — anchored to the diagnostic suffix so a filename merely
            # containing "socket ignored" cannot sneak through. Every other status still fails.
            diagnostic_lines = [line for line in stderr.splitlines() if line.strip()]
            tolerated = result.returncode == 2 and bool(diagnostic_lines) and all(
                line.endswith(": socket ignored") for line in diagnostic_lines)
            if not tolerated:
                raise _sync_error(f"SSH bulk download failed: {stderr}",
                                  f"File sync from {self.host}")

    def _ssh_delete(self, remote_paths: list[str]) -> None:
        self._run_ssh_checked(quoted_rm_command(remote_paths), 10, "remote rm failed",
                              f"Remote file cleanup on {self.host}")

    def _before_execute(self) -> None:
        if self._sync_manager is not None:
            self._sync_manager.sync()  # rate-limited internally

    def may_be_file_synced(self, path: str) -> bool:
        """Sync writes only under the remote ``~/.hermes`` (``_ssh_bulk_upload`` rejects anything
        else). Whatever this cannot classify for certain counts as covered: ``~`` and relative
        paths (the guard and the read may resolve them against different directories) and an
        unknown remote home. Compared case-insensitively, as on a default macOS volume."""
        if self._sync_manager is None:
            return False
        home = getattr(self, "_remote_home", None)
        # _detect_remote_home falls back to a guessed /home/<user> that need not be the real root.
        if not home or not getattr(self, "_remote_home_detected", False) or not posixpath.isabs(path):
            return True
        def canonical(p: str) -> str:
            # normpath keeps a POSIX '//' prefix that names the same file; macOS compares names
            # case- and Unicode-normalisation-insensitively.
            return unicodedata.normalize("NFC", "/" + posixpath.normpath(p).lstrip("/")).casefold()

        resolved, root = canonical(path), canonical(f"{home}/.hermes")
        return resolved == root or resolved.startswith(root + "/")

    def _run_bash(self, cmd_string: str, *, login: bool = False, timeout: int = 120,
                  stdin_data: str | None = None) -> subprocess.Popen:
        """Forward the passthrough allowlist (skill ``required_environment_variables`` +
        ``terminal.env_passthrough``) the way docker does: ``SendEnv`` carries the names, the ssh
        client's env carries the values, so secrets never enter the remote ``bash -c`` argv. The
        remote sshd must ``AcceptEnv`` them (#14091). Profile-scoped names missing from the active
        scope are unset remotely so a shared host cannot serve another profile's value."""
        values, unset_names = resolve_passthrough_env(hermes_env_loader=_load_hermes_env_vars)
        cmd = self._build_ssh_command(send_env=values) + bash_argv(shlex.quote(prepend_unset(cmd_string, unset_names)), login)
        client_env = client_env_with(values)
        return _popen_bash(cmd, stdin_data, env=client_env) if client_env is not None else _popen_bash(cmd, stdin_data)

    def __del__(self):
        # The fallback dir goes only after the LAST cleanup() (a poller still reconnects through a
        # cleaned-up env), and after it, not before: a weakref finalizer runs ahead of __del__ in
        # cyclic GC and at exit, and sync_back() would then connect through a deleted ControlPath.
        super().__del__()
        if getattr(self, "_owns_control_dir", False):
            shutil.rmtree(self.control_dir, ignore_errors=True)

    def cleanup(self):
        self.stop_all_processes()
        if self._sync_manager:
            logger.info("SSH: syncing files from sandbox...")
            self._sync_manager.sync_back()
        for socket in self._control_sockets():
            if not socket.exists():
                continue
            with contextlib.suppress(OSError, subprocess.SubprocessError):
                cmd = ["ssh", "-o", f"ControlPath={socket}", "-O", "exit", f"{self.user}@{self.host}"]
                subprocess.run(cmd, capture_output=True, timeout=5, stdin=subprocess.DEVNULL, check=False)
            with contextlib.suppress(OSError):
                socket.unlink()
