"""External providers receive logical workspace scope and notice delivery, not vendor logic."""
from types import SimpleNamespace

import pytest

from agent.agent_init import _GATEWAY_IDENTITY_PARAMS, _init_memory, _memory_provider_init_kwargs
from agent.runtime_cwd import reset_session_cwd, set_session_cwd
from tools.terminal_scope import (
    TerminalPolicyRefusal, TerminalPolicyUnavailable, reset_terminal_scope, set_terminal_scope,
)


PROVIDER = '''from agent.memory_provider import MemoryProvider
class RecordingProvider(MemoryProvider):
    name = "recording-bridge"
    def is_available(self): return True
    def initialize(self, session_id, **kwargs):
        self.received = kwargs
        self.session_id = session_id
    def get_tool_schemas(self): return []
'''


def make_agent():
    return SimpleNamespace(
        session_id="session", session_cwd="", _session_db=None,
        enabled_toolsets=[], disabled_toolsets=[], tools=[],
        **{f"_{key}": "" for key in _GATEWAY_IDENTITY_PARAMS},
    )


def test_external_provider_workspace_and_notices_follow_home_a_b_a(tmp_path, monkeypatch):
    homes = [tmp_path / "a", tmp_path / "b"]
    for home in homes:
        plugin = home / "plugins" / "recording-bridge"
        plugin.mkdir(parents=True)
        (plugin / "__init__.py").write_text(PROVIDER)
    session = set_session_cwd("")
    try:
        for home, backend, cwd in [(homes[0], "ssh", "/remote/a"),
                                   (homes[1], "local", str(tmp_path)),
                                   (homes[0], "ssh", "/remote/a")]:
            monkeypatch.setenv("HERMES_HOME", str(home))
            token = set_terminal_scope({"TERMINAL_ENV": backend, "TERMINAL_CWD": cwd})
            agent = make_agent()
            notices, clears = [], []
            agent._emit_notice = notices.append
            agent._emit_notice_clear = clears.append
            try:
                _init_memory(agent, {"memory": {"provider": "recording-bridge",
                    "memory_enabled": False, "user_profile_enabled": False},
                    "terminal": {"cwd": "/wrong", "backend": "docker"}}, False, "telegram")
                provider, = agent._memory_manager.providers
                received = provider.received
                assert received["cwd"] == received["agent_workspace"] == cwd
                assert received["workspace_backend"] == backend
                assert received["hermes_home"] == str(home)
                received["notice_callback"]("failed")
                received["notice_clear_callback"]("memory.write")
                assert notices == ["failed"] and clears == ["memory.write"]
            finally:
                reset_terminal_scope(token)
    finally:
        reset_session_cwd(session)


def test_configured_and_session_logical_paths_preserve_refusal_boundary():
    agent = make_agent()
    session = set_session_cwd("")
    token = set_terminal_scope({})
    try:
        kwargs = _memory_provider_init_kwargs(agent, "telegram",
            configured_cwd="Z:\\remote\\project", configured_backend="ssh")
        assert kwargs["cwd"] == "Z:\\remote\\project"
        assert kwargs["workspace_backend"] == "ssh"
        assert "notice_callback" not in kwargs
        agent.session_cwd = "/explicit"
        assert _memory_provider_init_kwargs(agent, "telegram")["cwd"] == "/explicit"
        refused = set_terminal_scope(TerminalPolicyRefusal("unreadable profile"))
        try:
            with pytest.raises(TerminalPolicyUnavailable):
                _memory_provider_init_kwargs(agent, "telegram")
        finally:
            reset_terminal_scope(refused)
    finally:
        reset_terminal_scope(token)
        reset_session_cwd(session)
