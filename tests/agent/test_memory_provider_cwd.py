"""Memory providers receive CLI workspace context without ambient gateway routing."""

from types import SimpleNamespace

import pytest

from agent.agent_init import _GATEWAY_IDENTITY_PARAMS
from agent.agent_init_memory import _memory_provider_init_kwargs
from agent import runtime_cwd


def _agent(cwd=None):
    return SimpleNamespace(
        session_id="cwd-test", session_cwd=cwd, _session_db=None,
        _emit_warning=None, _emit_status=None,
        **{f"_{name}": None for name in _GATEWAY_IDENTITY_PARAMS},
    )


@pytest.fixture(autouse=True)
def isolated_cwd(monkeypatch):
    token = runtime_cwd.set_session_cwd(None)
    monkeypatch.delenv("TERMINAL_CWD", raising=False)
    try:
        yield
    finally:
        runtime_cwd.reset_session_cwd(token)


@pytest.mark.parametrize("platform", ["cli", "", None])
def test_cli_provider_receives_launch_workspace(monkeypatch, tmp_path, platform):
    monkeypatch.chdir(tmp_path)
    kwargs = _memory_provider_init_kwargs(_agent(), platform)
    assert kwargs["platform"] == "cli"
    assert kwargs["cwd"] == str(tmp_path)


@pytest.mark.parametrize("platform", ["cli", "slack", "telegram", "cron", "subagent", "desktop"])
def test_explicit_session_cwd_remains_authoritative(monkeypatch, tmp_path, platform):
    monkeypatch.setenv("TERMINAL_CWD", str(tmp_path))
    # Explicit remote paths remain logical context, without host path validation.
    assert _memory_provider_init_kwargs(_agent("/remote/project"), platform)["cwd"] == "/remote/project"


@pytest.mark.parametrize("platform", ["slack", "telegram", "discord", "cron", "subagent", "desktop", "api"])
def test_non_cli_provider_does_not_inherit_ambient_workspace(monkeypatch, tmp_path, platform):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TERMINAL_CWD", str(tmp_path))
    assert "cwd" not in _memory_provider_init_kwargs(_agent(), platform)


@pytest.mark.parametrize("source", ["terminal", "session", "missing-terminal"])
def test_cli_provider_reuses_runtime_workspace_precedence(monkeypatch, tmp_path, source):
    launch = tmp_path / "launch"
    workspace = tmp_path / "workspace"
    launch.mkdir()
    workspace.mkdir()
    monkeypatch.chdir(launch)
    monkeypatch.setenv("TERMINAL_CWD", str(workspace))
    token = None
    if source == "session":
        token = runtime_cwd.set_session_cwd(str(launch))
    elif source == "missing-terminal":
        monkeypatch.setenv("TERMINAL_CWD", str(tmp_path / "missing"))
    try:
        expected = workspace if source == "terminal" else launch
        assert _memory_provider_init_kwargs(_agent(), "cli")["cwd"] == str(expected)
    finally:
        if token is not None:
            runtime_cwd.reset_session_cwd(token)


def test_cli_provider_retains_no_cwd_fallback_when_resolution_fails(monkeypatch):
    def deleted_cwd():
        raise OSError("working directory deleted")

    monkeypatch.setattr(runtime_cwd, "resolve_agent_cwd", deleted_cwd)
    assert "cwd" not in _memory_provider_init_kwargs(_agent(), "cli")
