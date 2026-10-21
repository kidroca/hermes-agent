"""Large individual payloads receive a size-derived SSH upload deadline."""

from unittest.mock import MagicMock

from tools.environments.ssh import SSHEnvironment


def test_large_upload_deadline_scales_with_staged_bytes(tmp_path, monkeypatch):
    env = SSHEnvironment.__new__(SSHEnvironment)
    env._remote_home = "/home/test"
    env.host = "test"
    env._run_ssh_checked = MagicMock()
    env._build_ssh_command = lambda: ["ssh", "test"]
    payload = tmp_path / "large"
    with payload.open("wb") as output:
        output.truncate(128 * 1024 * 1024)
    tar, ssh = MagicMock(), MagicMock()
    tar.returncode = ssh.returncode = 0
    tar.poll.return_value = 0
    tar.stderr.read.return_value = b""
    ssh.communicate.return_value = (b"", b"")
    monkeypatch.setattr("tools.environments.ssh.subprocess.Popen", MagicMock(side_effect=[tar, ssh]))
    env._ssh_bulk_upload([(str(payload), "/home/test/.hermes/cache/large")])
    assert ssh.communicate.call_args.kwargs["timeout"] >= 120 + 128
