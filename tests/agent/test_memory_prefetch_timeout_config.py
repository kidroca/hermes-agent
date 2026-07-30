"""Config propagation tests for the external-memory prefetch deadline."""

from unittest.mock import MagicMock

from run_agent import AIAgent


class _FakeOpenAI:
    def __init__(self, **kwargs):
        self.api_key = kwargs.get("api_key", "test")
        self.base_url = kwargs.get("base_url", "http://test")

    def close(self):
        pass


def test_memory_external_prefetch_timeout_default_is_eight_seconds():
    from hermes_cli.config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["memory"]["external_prefetch_timeout_seconds"] == 8


def test_memory_external_prefetch_timeout_reaches_manager(monkeypatch, tmp_path):
    """The generic memory config owns the external-provider turn deadline."""
    config = {
        "memory": {
            "provider": "fake-memory",
            "external_prefetch_timeout_seconds": 15,
        }
    }
    provider = MagicMock()
    provider.name = "fake-memory"
    provider.is_available.return_value = True
    provider.get_tool_schemas.return_value = []

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hm"))
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: config)
    monkeypatch.setattr("plugins.memory.load_memory_provider", lambda _name: provider)
    monkeypatch.setattr("run_agent.get_tool_definitions", lambda **_kwargs: [])
    monkeypatch.setattr("run_agent.check_toolset_requirements", lambda: {})
    monkeypatch.setattr("run_agent.OpenAI", _FakeOpenAI)

    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="gpt-4o",
        provider="openrouter",
        api_mode="chat_completions",
        max_iterations=1,
        quiet_mode=True,
        skip_context_files=True,
    )

    assert agent._memory_manager is not None
    assert agent._memory_manager._external_prefetch_timeout == 15
