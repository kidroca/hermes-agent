"""The terminal guard's remote script read must not wait on file sync for paths sync cannot touch.

Incident: an absolute interpreter path (``/Users/Shared/.../bin/python``) made the pre-execution
guard read the script remotely; that read ran the backend's full file sync first, which hung on a
degraded link until the guard deadline refused the command. Paths inside the synced tree (or
ambiguous ones) keep syncing so the guard never scans a stale copy of a file sync would replace.
"""

from unittest.mock import MagicMock

import pytest

from tools.environments import base
from tools.environments.ssh import SSHEnvironment
from tools.terminal_tool_guards import _read_script_for_guard


def _ssh_env(remote_home="/Users/u", syncing=True, cwd="/Users/u/work", detected=True):
    env = SSHEnvironment.__new__(SSHEnvironment)
    env._remote_home = remote_home
    env._remote_home_detected = detected
    env._sync_manager = MagicMock() if syncing else None
    env.cwd = cwd
    return env


@pytest.mark.parametrize("path, expected", [
    ("/Users/u/.hermes/skills/x/run.sh", True),
    ("/Users/u/.hermes", True),
    ("/Users/u/.hermes/../.hermes/skills/run.sh", True),
    ("/Users/U/.Hermes/skills/run.sh", True),    # case-insensitive volume (macOS default)
    ("/users/u/.HERMES", True),
    ("~/.hermes/skills/run.sh", True),           # ambiguous: stay conservative
    ("~/bin/tool", True),
    ("run.sh", True),                            # relative: guard and read may resolve differently
    ("./bin/../run.sh", True),
    ("/Users/Shared/AI/runtimes/x/bin/python", False),
    ("/Users/u/.hermes-other/run.sh", False),
    ("/Users/u/work/build.sh", False),
])
def test_ssh_paths_covered_by_file_sync(path, expected):
    assert _ssh_env().may_be_file_synced(path) is expected


@pytest.mark.parametrize("home, detected", [(None, True), ("", True), ("/home/u", False)])
def test_unknown_or_guessed_remote_home_counts_as_synced(home, detected):
    env = _ssh_env(remote_home=home, detected=detected)
    assert env.may_be_file_synced("/Users/Shared/AI/runtimes/x/bin/python") is True


def test_no_sync_manager_means_nothing_is_synced():
    assert _ssh_env(syncing=False).may_be_file_synced("/Users/u/.hermes/skills/run.sh") is False


def test_ssh_execute_path_honours_suppression():
    """SSH must reach the shared hook (no execute() override calling _before_execute directly)."""
    assert SSHEnvironment.execute is base.BaseEnvironment.execute
    env = _ssh_env()
    with base.skip_file_sync():
        env._run_before_execute()
    env._sync_manager.sync.assert_not_called()
    env._run_before_execute()
    env._sync_manager.sync.assert_called_once_with()


def test_base_default_is_conservative():
    assert base.BaseEnvironment.may_be_file_synced(MagicMock(), "/anything") is True


def test_before_execute_hook_is_skipped_only_while_suppressed():
    env = MagicMock()
    base.BaseEnvironment._run_before_execute(env)
    assert env._before_execute.call_count == 1
    with base.skip_file_sync():
        base.BaseEnvironment._run_before_execute(env)
    assert env._before_execute.call_count == 1
    base.BaseEnvironment._run_before_execute(env)
    assert env._before_execute.call_count == 2


class _RecordingEnv:
    def __init__(self, synced):
        self._synced = synced
        self.suppressed = []

    def may_be_file_synced(self, path):
        return self._synced

    def execute(self, command, **_):
        self.suppressed.append(base.file_sync_suppressed())
        return {"returncode": 0, "output": "echo hi\n"}


@pytest.mark.parametrize("synced, expect_suppressed", [(False, True), (True, False)])
def test_guard_read_suppresses_sync_only_outside_the_synced_tree(synced, expect_suppressed):
    env = _RecordingEnv(synced)
    text = _read_script_for_guard(env, "/remote/cwd", "/nonexistent-on-host/script.sh", 1024)
    assert text == "echo hi\n"
    assert env.suppressed == [expect_suppressed]
    assert base.file_sync_suppressed() is False  # never leaks past the read


def test_guard_read_on_a_backend_without_the_hook_keeps_syncing():
    env = MagicMock(spec=["execute"])
    env.execute.side_effect = lambda *a, **k: (
        {"returncode": 0, "output": str(base.file_sync_suppressed())})
    assert _read_script_for_guard(env, "/remote/cwd", "/nonexistent-on-host/s.sh", 1024) == "False"
