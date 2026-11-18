"""The SSH tar upload stream is gzip-compressed (the support tree is mostly text)."""


import subprocess
from unittest.mock import MagicMock

import pytest

from tools.environments import ssh as ssh_env


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


@pytest.mark.parametrize("gzip_ok", [True, False])
def test_ssh_upload_is_compressed_only_when_the_remote_has_gzip(env, tmp_path, monkeypatch, gzip_ok):
    host = tmp_path / "page.md"
    host.write_bytes(b"x" * 10000)
    popen_cmds = []

    def popen(cmd, **kw):
        popen_cmds.append(cmd)
        proc = MagicMock()
        proc.returncode = 0
        proc.poll.return_value = 0
        proc.communicate.return_value = (b"", b"")
        proc.stderr.read.return_value = b""
        return proc

    monkeypatch.setattr(ssh_env.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    monkeypatch.setattr(ssh_env.subprocess, "Popen", popen)
    env._remote_gzip = gzip_ok
    env._ssh_bulk_upload([(str(host), "/Users/u/.hermes/cache/web/page.md")])
    tar_cmd, ssh_cmd = popen_cmds
    assert ("-czhf" if gzip_ok else "-chf") in tar_cmd
    assert ssh_cmd[-1] == f"tar x{'z' if gzip_ok else ''}f - -C /Users/u/.hermes"


def test_upload_without_a_listing_state_stays_uncompressed(tmp_path, monkeypatch):
    env = ssh_env.SSHEnvironment.__new__(ssh_env.SSHEnvironment)  # no __init__: no gzip proof
    env._remote_home, env.host = "/home/t", "t"
    env._run_ssh_checked = MagicMock()
    env._build_ssh_command = lambda: ["ssh", "t"]
    host = tmp_path / "f"
    host.write_bytes(b"x")
    procs = [MagicMock(returncode=0), MagicMock(returncode=0)]
    procs[0].poll.return_value = 0
    procs[0].stderr.read.return_value = b""
    procs[1].communicate.return_value = (b"", b"")
    popen = MagicMock(side_effect=procs)
    monkeypatch.setattr(ssh_env.subprocess, "Popen", popen)
    env._ssh_bulk_upload([(str(host), "/home/t/.hermes/cache/f")])
    assert popen.call_args_list[1].args[0][-1] == "tar xf - -C /home/t/.hermes"
