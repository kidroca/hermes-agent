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


def test_ssh_upload_stream_is_gzip_compressed(env, tmp_path, monkeypatch):
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
    env._ssh_bulk_upload([(str(host), "/Users/u/.hermes/cache/web/page.md")])
    tar_cmd, ssh_cmd = popen_cmds
    assert "-czhf" in tar_cmd
    assert ssh_cmd[-1] == "tar xzf - -C /Users/u/.hermes"
