"""Regression coverage for queued follow-up memory-query propagation."""

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import gateway.run as gateway_run
from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
)
from gateway.session import SessionSource


class _CaptureAdapter(BasePlatformAdapter):
    def __init__(self):
        super().__init__(PlatformConfig(enabled=True, token="test"), Platform.TELEGRAM)

    async def connect(self, *, is_reconnect=False):
        return True

    async def disconnect(self):
        return None

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        return SendResult(success=True, message_id="m1")

    async def edit_message(
        self, chat_id, message_id, content, *, finalize=False
    ):
        return SendResult(success=True, message_id=message_id)

    async def send_typing(self, chat_id, metadata=None):
        return None

    async def stop_typing(self, chat_id):
        return None

    async def get_chat_info(self, chat_id):
        return {"id": chat_id}


class _FakeAgent:
    def __init__(self, **kwargs):
        self.tools = []
        self._interrupt_requested = False

    @property
    def is_interrupted(self):
        return self._interrupt_requested

    def run_conversation(self, message, conversation_history=None, task_id=None, **kwargs):
        return {
            "final_response": "first answer",
            "messages": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "first answer"},
            ],
            "api_calls": 1,
        }


@pytest.mark.asyncio
async def test_queued_followup_preserves_memory_query_text(monkeypatch, tmp_path):
    """Reply enrichment must not replace the authored recall query when busy."""
    fake_run_agent = types.ModuleType("run_agent")
    fake_run_agent.AIAgent = _FakeAgent
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)
    monkeypatch.setattr(
        gateway_run, "_resolve_runtime_agent_kwargs", lambda: {"api_key": "fake"}
    )

    adapter = _CaptureAdapter()
    runner = object.__new__(gateway_run.GatewayRunner)
    runner.adapters = {adapter.platform: adapter}
    runner._voice_mode = {}
    runner._prefill_messages = []
    runner._ephemeral_system_prompt = ""
    runner._reasoning_config = None
    runner._provider_routing = {}
    runner._fallback_model = None
    runner._session_db = None
    runner._running_agents = {}
    runner._session_run_generation = {}
    runner._queued_events = {}
    runner._delivery_states = {}
    runner._draining = False
    runner.hooks = SimpleNamespace(loaded_hooks=False)
    runner.config = SimpleNamespace(
        thread_sessions_per_user=False,
        group_sessions_per_user=False,
        stt_enabled=False,
    )
    runner._refresh_agent_cache_message_count = AsyncMock()
    enriched = '[Replying to: "long old context"]\n\nok'
    runner._prepare_profile_scoped_inbound_message_text = AsyncMock(
        return_value=enriched
    )

    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="-1001",
        chat_type="group",
        thread_id="17585",
    )
    session_key = "agent:main:telegram:group:-1001:17585"
    adapter._pending_messages[session_key] = MessageEvent(
        text=enriched,
        message_type=MessageType.TEXT,
        source=source,
        message_id="followup-1",
        memory_query_text="ok",
    )

    recursive_call = AsyncMock(
        return_value={
            "final_response": "second answer",
            "messages": [],
            "history_offset": 0,
        }
    )
    runner._run_agent = recursive_call

    await gateway_run.GatewayRunner._run_agent_inner(
        runner,
        message="first long question",
        context_prompt="",
        history=[],
        source=source,
        session_id="sess-busy-memory-query",
        session_key=session_key,
        memory_query_message="first long question",
    )

    recursive_call.assert_awaited_once()
    call = recursive_call.await_args.kwargs
    assert call["message"] == enriched
    assert call["memory_query_message"] == "ok"
