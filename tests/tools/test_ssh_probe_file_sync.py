"""Regression coverage for SSH prompt probes that must not synchronize files."""

from unittest.mock import MagicMock

from agent import prompt_builder
from tools.environments import ssh as ssh_env


def _stub_ssh_connection(monkeypatch):
    monkeypatch.setattr(ssh_env, "_ensure_ssh_available", lambda: None)
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_establish_connection", lambda self: None)
    monkeypatch.setattr(
        ssh_env.SSHEnvironment,
        "_detect_remote_home",
        lambda self: "/home/alice",
    )
    monkeypatch.setattr(ssh_env.SSHEnvironment, "init_session", lambda self: None)


def test_ssh_prompt_probe_disables_file_sync(monkeypatch):
    """The metadata-only system-prompt probe must not request SSH file sync."""
    prompt_builder._clear_backend_probe_cache()
    monkeypatch.setenv("TERMINAL_ENV", "ssh")

    created = {}

    class ProbeEnvironment:
        def execute(self, _command, timeout=None):
            return {
                "returncode": 0,
                "output": (
                    "os=Darwin\nkernel=25.6.0\nhome=/Users/alice\n"
                    "cwd=/Users/alice\nuser=alice\n"
                ),
            }

    def create_environment(**kwargs):
        created.update(kwargs)
        return ProbeEnvironment()

    import tools.terminal_tool as terminal_tool

    monkeypatch.setattr(terminal_tool, "_create_environment", create_environment)
    monkeypatch.setattr(
        terminal_tool,
        "_get_env_config",
        lambda: {
            "ssh_host": "mac.example",
            "ssh_user": "alice",
            "ssh_port": 22,
            "ssh_key": "",
            "ssh_persistent": True,
            "cwd": "~",
            "timeout": 180,
            "host_cwd": None,
        },
    )

    result = prompt_builder._probe_remote_backend("ssh")

    assert result is not None
    assert created["ssh_config"]["sync_files"] is False


def test_terminal_factory_forwards_probe_sync_policy(monkeypatch):
    """The generic environment factory must carry the probe policy to SSH."""
    import tools.terminal_tool as terminal_tool

    constructor = MagicMock(return_value=object())
    monkeypatch.setattr(terminal_tool, "_SSHEnvironment", constructor)

    terminal_tool._create_environment(
        env_type="ssh",
        image="",
        cwd="~",
        timeout=180,
        ssh_config={
            "host": "mac.example",
            "user": "alice",
            "port": 22,
            "key": "",
            "sync_files": False,
        },
    )

    assert constructor.call_args.kwargs["sync_files"] is False


def test_ssh_environment_can_skip_all_file_sync(monkeypatch):
    """A metadata-only SSH environment must not scan, upload, or sync back files."""
    _stub_ssh_connection(monkeypatch)
    ensure_dirs = MagicMock()
    manager_factory = MagicMock()
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_ensure_remote_dirs", ensure_dirs)
    monkeypatch.setattr(ssh_env, "FileSyncManager", manager_factory)

    env = ssh_env.SSHEnvironment(host="mac.example", user="alice", sync_files=False)
    env._before_execute()
    env.cleanup()

    ensure_dirs.assert_not_called()
    manager_factory.assert_not_called()


def test_ssh_environment_keeps_default_sync_behavior(monkeypatch):
    """Real SSH tool environments still bootstrap and re-check synchronized files."""
    _stub_ssh_connection(monkeypatch)
    ensure_dirs = MagicMock()
    sync_manager = MagicMock()
    monkeypatch.setattr(ssh_env.SSHEnvironment, "_ensure_remote_dirs", ensure_dirs)
    monkeypatch.setattr(ssh_env, "FileSyncManager", lambda **_kwargs: sync_manager)

    env = ssh_env.SSHEnvironment(host="mac.example", user="alice")
    env._before_execute()

    ensure_dirs.assert_called_once_with()
    assert sync_manager.sync.call_args_list[0].kwargs == {"force": True}
    assert sync_manager.sync.call_args_list[1].kwargs == {}
