"""External providers use the existing structured notice rail, not workspace overrides."""
from types import SimpleNamespace

import pytest

from agent.agent_init import _GATEWAY_IDENTITY_PARAMS, _init_memory, _memory_provider_init_kwargs
from agent.credits_tracker import AgentNotice
from agent.memory_manager import MemoryManager
from agent.status_output import StatusOutputMixin


PROVIDER = '''from agent.memory_provider import MemoryProvider
class RecordingProvider(MemoryProvider):
    name = "recording-bridge"
    def is_available(self): return True
    def initialize(self, session_id, **kwargs):
        self.received = kwargs
        self.session_id = session_id
    def get_tool_schemas(self): return []
'''


class NoticeAgent(StatusOutputMixin, SimpleNamespace):
    pass


def make_agent(cls: type[SimpleNamespace] = NoticeAgent):
    return cls(
        session_id="session", session_cwd="", _session_db=None,
        enabled_toolsets=[], disabled_toolsets=[], tools=[],
        **{f"_{key}": "" for key in _GATEWAY_IDENTITY_PARAMS},
    )


@pytest.mark.parametrize("platform", ["cli", "telegram", "tui", "acp"])
def test_external_provider_delivers_structured_notice_and_recovery(tmp_path, monkeypatch, platform):
    plugin = tmp_path / "plugins" / "recording-bridge"
    plugin.mkdir(parents=True)
    (plugin / "__init__.py").write_text(PROVIDER)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    agent = make_agent()
    events = []
    agent.notice_callback = lambda notice: events.append(("notice", notice))
    agent.notice_clear_callback = lambda key: events.append(("clear", key))
    _init_memory(agent, {"memory": {"provider": "recording-bridge",
        "memory_enabled": False, "user_profile_enabled": False}}, False, platform)
    assert isinstance(agent._memory_manager, MemoryManager)
    provider, = agent._memory_manager.providers
    assert getattr(provider, "session_id") == agent.session_id
    callbacks = getattr(provider, "received")
    assert callbacks["hermes_home"] == str(tmp_path)
    assert ("status_callback" in callbacks) == (platform == "cli")
    failed = AgentNotice("Retention failed", level="error", key="memory.write")
    recovered = AgentNotice("Retention recovered", level="success", kind="ttl", ttl_ms=5000)
    callbacks["notice_callback"](failed)
    callbacks["notice_clear_callback"](failed.key)
    callbacks["notice_callback"](recovered)
    assert events == [("notice", failed), ("clear", failed.key), ("notice", recovered)]
    assert events[0][1] is failed

    # Driver failures must not escape into a provider operation.
    def broken_sink(_value):
        raise RuntimeError("driver gone")
    agent.notice_callback = agent.notice_clear_callback = broken_sink
    callbacks["notice_callback"](failed)
    callbacks["notice_clear_callback"](failed.key)
    agent.notice_callback = agent.notice_clear_callback = None
    callbacks["notice_callback"](failed)
    callbacks["notice_clear_callback"](failed.key)
    assert events == [("notice", failed), ("clear", failed.key), ("notice", recovered)]
    agent._memory_manager.shutdown_all()


@pytest.mark.parametrize("callback", [None, "not callable"])
def test_agents_without_notice_methods_do_not_advertise_callbacks(callback):
    agent = make_agent(SimpleNamespace)
    agent._emit_notice = agent._emit_notice_clear = callback
    kwargs = _memory_provider_init_kwargs(agent, "telegram")
    assert "notice_callback" not in kwargs
    assert "notice_clear_callback" not in kwargs
