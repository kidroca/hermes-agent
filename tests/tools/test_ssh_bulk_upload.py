"""Tests for SSH bulk upload via tar pipe."""

import os
import ntpath
import shlex
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.environments import ssh as ssh_env
from tools.environments.ssh import SSHEnvironment


def _mock_proc(*, returncode=0, poll_return=0, communicate_return=(b"", b""),
               stderr_read=b""):
    """Create a MagicMock mimicking subprocess.Popen for tar/ssh pipes."""
    m = MagicMock()
    m.stdout = MagicMock()
    m.returncode = returncode
    m.poll.return_value = poll_return
    m.communicate.return_value = communicate_return
    m.stderr = MagicMock()
    m.stderr.read.return_value = stderr_read
    return m


@pytest.fixture
def mock_env(monkeypatch):
    """Create an SSHEnvironment with mocked connection/sync."""
    monkeypatch.setattr(ssh_env.shutil, "which", lambda _name: "/usr/bin/ssh")
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_establish_connection", lambda self: None)
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_detect_remote_home", lambda self: "/home/testuser")
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_ensure_remote_dirs", lambda self: None)
    monkeypatch.setattr(ssh_env.SSHEnvironment, "init_session", lambda self: None)
    monkeypatch.setattr(
        ssh_env, "FileSyncManager",
        lambda **kw: type("M", (), {"sync": lambda self, **k: None})(),
    )
    return SSHEnvironment(host="example.com", user="testuser")


class TestSSHBulkUpload:
    """Unit tests for _ssh_bulk_upload — tar pipe mechanics."""

    def test_empty_files_is_noop(self, mock_env):
        """Empty file list should not spawn any subprocesses."""
        with patch.object(subprocess, "run") as mock_run, \
             patch.object(subprocess, "Popen") as mock_popen:
            mock_env._ssh_bulk_upload([])
            mock_run.assert_not_called()
            mock_popen.assert_not_called()

    def test_remote_archive_entries_always_use_posix_paths(self):
        assert ssh_env._remote_sync_relative_path(
            "/home/testuser/.hermes/skills/example/SKILL.md",
            "/home/testuser/.hermes",
        ) == "skills/example/SKILL.md"

    def test_windows_staging_preserves_posix_components(self):
        assert ssh_env._local_sync_staging_path(
            r"C:\stage",
            "skills/example/SKILL.md",
            path_module=ntpath,
        ) == r"C:\stage\skills\example\SKILL.md"

    @pytest.mark.parametrize("relative", [
        r"skills\..\..\escape",
        "C:/escape",
        "skills/file:stream",
        "skills/CON",
        "skills/trailing.",
        "skills/trailing ",
        "skills/question?",
    ])
    def test_windows_staging_rejects_unrepresentable_remote_names(self, relative):
        with pytest.raises(RuntimeError, match="not representable on Windows"):
            ssh_env._local_sync_staging_path(
                r"C:\stage",
                relative,
                path_module=ntpath,
            )

    @pytest.mark.parametrize("remote_path", [
        "/home/testuser/.hermes",
        "/home/testuser",
        "/home/testuser/.config/settings.json",
    ])
    def test_remote_archive_entries_cannot_escape_sync_base(self, remote_path):
        with pytest.raises(RuntimeError, match="escapes sync base"):
            ssh_env._remote_sync_relative_path(
                remote_path,
                "/home/testuser/.hermes",
            )

    def test_invalid_remote_destination_is_rejected_before_remote_mkdir(self, mock_env, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("content")

        with patch.object(mock_env, "_run_ssh_checked") as remote_command:
            with pytest.raises(RuntimeError, match="escapes sync base"):
                mock_env._ssh_bulk_upload([(str(source), "/tmp/escape/file.txt")])

        remote_command.assert_not_called()

    def test_mkdir_batched_into_single_call(self, mock_env, tmp_path):
        """All parent directories should be created in one SSH call."""
        # Create test files
        f1 = tmp_path / "a.txt"
        f1.write_text("aaa")
        f2 = tmp_path / "b.txt"
        f2.write_text("bbb")

        files = [
            (str(f1), "/home/testuser/.hermes/skills/a.txt"),
            (str(f2), "/home/testuser/.hermes/credentials/b.txt"),
        ]

        # Mock subprocess.run for mkdir and Popen for tar pipe
        mock_run = MagicMock(return_value=subprocess.CompletedProcess([], 0))

        def make_proc(cmd, **kwargs):
            m = MagicMock()
            m.stdout = MagicMock()
            m.returncode = 0
            m.poll.return_value = 0
            m.communicate.return_value = (b"", b"")
            m.stderr = MagicMock()
            m.stderr.read.return_value = b""
            return m

        with patch.object(subprocess, "run", mock_run), \
             patch.object(subprocess, "Popen", side_effect=make_proc):
            mock_env._ssh_bulk_upload(files)

        # Exactly one subprocess.run call for mkdir
        assert mock_run.call_count == 1
        mkdir_cmd = mock_run.call_args[0][0]
        # Should contain mkdir -p with both parent dirs
        mkdir_str = " ".join(mkdir_cmd)
        assert "mkdir -p" in mkdir_str
        assert "/home/testuser/.hermes/skills" in mkdir_str
        assert "/home/testuser/.hermes/credentials" in mkdir_str

    def test_staging_symlinks_mirror_remote_layout(self, mock_env, tmp_path):
        """Staged file in staging dir should mirror the remote path structure.

        On platforms where symlinks are available (Linux/macOS) the staged
        entry is a symlink; on Windows it may be a regular copy.  Either way
        the file must exist at the expected path and contain the right data.
        """
        f1 = tmp_path / "local_a.txt"
        f1.write_text("content a")

        files = [
            (str(f1), "/home/testuser/.hermes/skills/my_skill.md"),
        ]

        staging_paths = []

        def capture_tar_cmd(cmd, **kwargs):
            if cmd[0] == "tar":
                # Capture the staging dir from -C argument
                c_idx = cmd.index("-C")
                staging_dir = cmd[c_idx + 1]
                # Check the staged entry exists at the base-relative path
                expected = os.path.join(staging_dir, "skills/my_skill.md")
                staging_paths.append(expected)
                # File must exist (either as symlink or copy)
                assert os.path.exists(expected), f"Expected staged file at {expected}"
                # Content must match the source
                with open(expected, "r") as fh:
                    assert fh.read() == "content a"

            mock = MagicMock()
            mock.stdout = MagicMock()
            mock.returncode = 0
            mock.poll.return_value = 0
            mock.communicate.return_value = (b"", b"")
            mock.stderr = MagicMock()
            mock.stderr.read.return_value = b""
            return mock

        with patch.object(subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(subprocess, "Popen", side_effect=capture_tar_cmd):
            mock_env._ssh_bulk_upload(files)

        assert len(staging_paths) == 1, "tar command should have been called"


    @pytest.mark.require_symlinks
    def test_bulk_upload_never_stages_remote_home_prefix(self, mock_env, tmp_path):
        """Regression: do not archive /home/<user> path components."""
        f1 = tmp_path / "nested.txt"
        f1.write_text("nested")
        files = [(str(f1), "/home/testuser/.hermes/cache/nested.txt")]

        def capture_tar_cmd(cmd, **kwargs):
            if cmd[0] == "tar":
                c_idx = cmd.index("-C")
                staging_dir = cmd[c_idx + 1]
                assert not os.path.exists(os.path.join(staging_dir, "home"))
                expected = os.path.join(staging_dir, "cache/nested.txt")
                assert os.path.islink(expected)

            mock = MagicMock()
            mock.stdout = MagicMock()
            mock.returncode = 0
            mock.poll.return_value = 0
            mock.communicate.return_value = (b"", b"")
            mock.stderr = MagicMock()
            mock.stderr.read.return_value = b""
            return mock

        with patch.object(subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(subprocess, "Popen", side_effect=capture_tar_cmd):
            mock_env._ssh_bulk_upload(files)


    def test_tar_pipe_uses_file_manifest_and_preserves_parent_metadata(
        self, mock_env, tmp_path, monkeypatch
    ):
        """The real local tar contains files only; remote extraction uses portable flags."""
        monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/test-agent.sock")
        f1 = tmp_path / "x.txt"
        f1.write_text("x")
        f2 = tmp_path / "y.txt"
        f2.write_text("y")
        files = [
            (str(f1), "/home/testuser/.hermes/cache/x.txt"),
            (str(f2), "/home/testuser/.hermes/skills/y.txt"),
        ]
        tar_calls = []
        tar_members = []
        ssh_commands = []
        real_popen = subprocess.Popen

        def capture_popen(cmd, **kwargs):
            if cmd[0] == "tar":
                manifest_path = cmd[cmd.index("-T") + 1]
                archive_path = tmp_path / "payload.tar"
                archive_cmd = list(cmd)
                archive_cmd[archive_cmd.index("-")] = str(archive_path)
                archive_proc = real_popen(
                    archive_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=kwargs.get("env"),
                )
                _, archive_stderr = archive_proc.communicate()
                assert archive_proc.returncode == 0, archive_stderr.decode()
                with tarfile.open(archive_path) as archive:
                    tar_members.extend(
                        (member.name, member.isfile()) for member in archive.getmembers()
                    )
                tar_calls.append({
                    "cmd": cmd,
                    "env": kwargs.get("env", {}),
                    "manifest": Path(manifest_path).read_bytes(),
                })
            else:
                ssh_commands.append(cmd)
            return _mock_proc()

        with patch.object(subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(subprocess, "Popen", side_effect=capture_popen):
            mock_env._ssh_bulk_upload(files)

        assert len(tar_calls) == 1
        assert tar_calls[0]["env"]["COPYFILE_DISABLE"] == "1"
        assert tar_calls[0]["env"]["HOME"] == os.environ["HOME"]
        assert tar_calls[0]["env"]["SSH_AUTH_SOCK"] == "/tmp/test-agent.sock"
        assert "--no-xattrs" in tar_calls[0]["cmd"]
        assert tar_calls[0]["manifest"].split(b"\0") == [
            b"cache/x.txt",
            b"skills/y.txt",
            b"",
        ]
        assert tar_members == [
            ("cache/x.txt", True),
            ("skills/y.txt", True),
        ]
        assert ssh_commands[0][-1] == "tar xf - -C /home/testuser/.hermes"
        assert "--no-overwrite-dir" not in " ".join(ssh_commands[0])


    @pytest.mark.platforms("linux")
    @pytest.mark.parametrize("creator", [shutil.which("tar"), shutil.which("bsdtar")], ids=["gnu", "bsd"])
    @pytest.mark.parametrize("extractor", [shutil.which("tar"), shutil.which("bsdtar")], ids=["gnu", "bsd"])
    @pytest.mark.parametrize("names", [
        ["skills/file.txt"],
        ["skills/name\n.", r"skills/back\slash", " spaced name ", "--no-recursion"],
        [".hermes-tar-entries"],
    ], ids=["ordinary", "literal-pathnames", "manifest-collision"])
    def test_real_upload_preserves_files_and_directory_modes(
        self, mock_env, tmp_path, monkeypatch, creator, extractor, names
    ):
        """Exercise the actual tar pipe; only the SSH transport is replaced locally."""
        # Resolve binaries during collection, before mock_env patches shutil.which.
        create_bin, extract_bin = creator, extractor
        if not create_bin or not extract_bin:
            pytest.skip("Both requested tar implementations must be installed")
        home = tmp_path / "remote home"
        base = home / ".hermes"
        skills = base / "skills"
        skills.mkdir(parents=True)
        for directory, mode in [(home, 0o751), (base, 0o711), (skills, 0o700)]:
            directory.chmod(mode)
        modes = {p: stat.S_IMODE(p.stat().st_mode) for p in (home, base, skills)}
        mock_env._remote_home = str(home)
        monkeypatch.setattr(mock_env, "_run_ssh_checked", lambda *args: None)
        real_popen = subprocess.Popen
        files, originals = [], {}
        for index, name in enumerate(names):
            source = tmp_path / f"source-{index}"
            payload = f"new payload {index}".encode()
            source.write_bytes(payload)
            destination = base / name
            destination.write_bytes(b"previous payload")
            files.append((str(source), str(destination)))
            originals[source] = payload

        def local_transport(cmd, **kwargs):
            if cmd[0] == "tar":
                return real_popen([create_bin, *cmd[1:]], **kwargs)
            remote = shlex.split(cmd[-1])
            assert remote[0] == "tar"
            return real_popen([extract_bin, *remote[1:]], **kwargs)

        with patch.object(subprocess, "Popen", side_effect=local_transport):
            mock_env._ssh_bulk_upload(files)
        assert {p: p.read_bytes() for p in originals} == originals
        for source, destination in files:
            assert Path(destination).read_bytes() == originals[Path(source)]
        assert {p: stat.S_IMODE(p.stat().st_mode) for p in modes} == modes
        assert {str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()} == set(names)

    def test_timeout_kills_both_processes(self, mock_env, tmp_path):
        """TimeoutExpired during communicate should kill both processes."""
        f1 = tmp_path / "t.txt"
        f1.write_text("t")
        files = [(str(f1), "/home/testuser/.hermes/skills/t.txt")]

        mock_tar = MagicMock()
        mock_tar.stdout = MagicMock()
        mock_tar.returncode = None
        mock_tar.poll.return_value = None

        mock_ssh = MagicMock()
        mock_ssh.communicate.side_effect = subprocess.TimeoutExpired("ssh", 120)
        mock_ssh.returncode = None

        def make_proc(cmd, **kwargs):
            if cmd[0] == "tar":
                return mock_tar
            return mock_ssh

        with patch.object(subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(subprocess, "Popen", side_effect=make_proc):
            with pytest.raises(RuntimeError, match="SSH bulk upload timed out"):
                mock_env._ssh_bulk_upload(files)

        mock_tar.kill.assert_called_once()
        mock_ssh.kill.assert_called_once()






class TestSSHBulkUploadEdgeCases:
    """Edge cases for _ssh_bulk_upload."""

    def test_ssh_popen_failure_kills_tar(self, mock_env, tmp_path):
        """If SSH Popen raises, tar process must be killed and cleaned up."""
        f1 = tmp_path / "e.txt"
        f1.write_text("e")
        files = [(str(f1), "/home/testuser/.hermes/skills/e.txt")]

        mock_tar = _mock_proc()

        call_count = 0

        def failing_ssh_popen(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_tar  # tar Popen succeeds
            raise OSError("SSH binary not found")

        with patch.object(subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(subprocess, "Popen", side_effect=failing_ssh_popen):
            with pytest.raises(OSError, match="SSH binary not found"):
                mock_env._ssh_bulk_upload(files)

        mock_tar.kill.assert_called_once()
        mock_tar.wait.assert_called_once()
