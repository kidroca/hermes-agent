"""A new manager asks the remote which bytes it already holds, so a fresh session does not
re-upload the whole support tree (every lad-studio cold start pushed ~150 MB)."""


import hashlib
import subprocess
from unittest.mock import MagicMock

import pytest

from tools.environments import ssh as ssh_env
from tools.environments.file_sync import FileSyncManager


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _files(tmp_path, **contents):
    pairs = []
    for name, text in contents.items():
        host = tmp_path / name
        host.write_bytes(text.encode())
        pairs.append((str(host), f"/remote/.hermes/{name}"))
    return pairs


def _uploaded(bulk):
    return sorted(remote for call in bulk.call_args_list for _, remote in call.args[0])


def test_fresh_manager_uploads_only_what_the_remote_lacks(tmp_path):
    pairs = _files(tmp_path, same="kept", changed="new", missing="absent")
    remote = {"/remote/.hermes/same": _sha(b"kept"), "/remote/.hermes/changed": _sha(b"old")}
    bulk = MagicMock()
    hashes_fn = MagicMock(return_value=remote)
    mgr = FileSyncManager(lambda: pairs, MagicMock(), MagicMock(), bulk_upload_fn=bulk,
                          remote_hashes_fn=hashes_fn)
    mgr.sync(force=True)
    assert _uploaded(bulk) == ["/remote/.hermes/changed", "/remote/.hermes/missing"]
    # The matched file counts as pushed: sync-back must not treat its remote copy as a change.
    assert mgr._pushed_hashes["/remote/.hermes/same"] == _sha(b"kept")

    mgr.sync(force=True)
    hashes_fn.assert_called_once()  # one remote listing per manager, not per cycle


def test_host_edit_after_a_manifest_match_is_uploaded(tmp_path):
    pairs = _files(tmp_path, same="kept")
    bulk = MagicMock()
    mgr = FileSyncManager(lambda: pairs, MagicMock(), MagicMock(), bulk_upload_fn=bulk,
                          remote_hashes_fn=lambda: {"/remote/.hermes/same": _sha(b"kept")})
    mgr.sync(force=True)
    assert bulk.call_count == 0
    (tmp_path / "same").write_bytes(b"edited on the host")
    mgr.sync(force=True)
    assert _uploaded(bulk) == ["/remote/.hermes/same"]


def test_failed_remote_listing_falls_back_to_a_full_upload(tmp_path, caplog):
    pairs = _files(tmp_path, a="a", b="b")
    bulk = MagicMock()
    hashes_fn = MagicMock(side_effect=RuntimeError("link down"))
    mgr = FileSyncManager(lambda: pairs, MagicMock(), MagicMock(), bulk_upload_fn=bulk,
                          remote_hashes_fn=hashes_fn)
    mgr.sync(force=True)
    assert _uploaded(bulk) == ["/remote/.hermes/a", "/remote/.hermes/b"]
    assert "remote hash listing failed" in caplog.text
    mgr.sync(force=True)
    hashes_fn.assert_called_once()  # no listing retry storm on a degraded link


# --- SSH remote listing ----------------------------------------------------------------

@pytest.fixture
def env(monkeypatch):
    monkeypatch.setattr(ssh_env.shutil, "which", lambda _name: "/usr/bin/ssh")
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_establish_connection", lambda self: None)
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_detect_remote_home", lambda self: "/Users/u")
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_ensure_remote_dirs", lambda self: None)
    monkeypatch.setattr(ssh_env.SSHEnvironment, "init_session", lambda self: None)
    captured = {}

    def manager(**kw):
        captured.update(kw)
        return MagicMock()

    monkeypatch.setattr(ssh_env, "FileSyncManager", manager)
    environment = ssh_env.SSHEnvironment(host="example.com", user="u")
    environment.captured_manager_kwargs = captured
    return environment


def test_ssh_wires_the_remote_listing(env):
    assert env.captured_manager_kwargs["remote_hashes_fn"] == env._ssh_remote_hashes


def test_ssh_remote_listing_parses_hash_output(env, monkeypatch):
    good, other = "a" * 64, "b" * 64
    stdout = (f"{good}  ./skills/x/SKILL.md\n"
              f"{other}  ./cache/web/page one.md\n"
              f"\\{good}  ./odd\\nname\n"         # escaped name (backslash/newline): skip
              f"{good}  -\n"                      # empty xargs run hashing stdin: skip
              f"nothex  ./bogus\n").encode()
    calls = []

    def run(cmd, **kw):
        calls.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 0, stdout, b"")

    monkeypatch.setattr(ssh_env.subprocess, "run", run)
    assert env._ssh_remote_hashes() == {
        "/Users/u/.hermes/skills/x/SKILL.md": good,
        "/Users/u/.hermes/cache/web/page one.md": other,
    }
    cmd, kw = calls[0]
    assert cmd[-1].startswith("sh -c ")  # never rely on the remote login shell's word splitting
    assert kw["stdin"] is subprocess.DEVNULL and kw["timeout"] > 0


def test_ssh_remote_listing_raises_on_transport_failure(env, monkeypatch):
    monkeypatch.setattr(ssh_env.subprocess, "run",
                        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 255, b"", b"timeout"))
    with pytest.raises(Exception):
        env._ssh_remote_hashes()


def test_ssh_remote_listing_script_runs_under_sh(env, tmp_path):
    """Run the real listing script locally against a fake remote tree."""
    base = tmp_path / ".hermes"
    (base / "skills").mkdir(parents=True)
    (base / "skills" / "a.md").write_bytes(b"alpha")
    (base / "with space.md").write_bytes(b"beta")
    script = env._remote_hash_script(str(base))
    out = subprocess.run(["sh", "-c", script], capture_output=True, check=False).stdout
    parsed = ssh_env._parse_remote_hashes(out, str(base))
    assert parsed == {f"{base}/skills/a.md": _sha(b"alpha"), f"{base}/with space.md": _sha(b"beta")}


def test_ssh_remote_listing_of_a_missing_tree_is_empty(env, tmp_path):
    script = env._remote_hash_script(str(tmp_path / "absent"))
    out = subprocess.run(["sh", "-c", script], capture_output=True, check=False)
    assert ssh_env._parse_remote_hashes(out.stdout, str(tmp_path / "absent")) == {}
