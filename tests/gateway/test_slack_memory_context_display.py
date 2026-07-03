"""Slack gateway memory-context debug display tests."""

import asyncio

from gateway.config import Platform
from gateway.platforms.base import BasePlatformAdapter, SendResult
from gateway.run import (
    _GATEWAY_MEMORY_CONTEXT_MAX_CHARS,
    _format_gateway_memory_context,
    _resolve_gateway_memory_context_display,
    _send_gateway_memory_context_display,
)
from gateway.session import SessionSource


class _FakeSlackAdapter:
    def __init__(self, *, private_success: bool = True):
        self.private_success = private_success
        self.private_calls = []
        self.public_calls = []

    async def send_private_notice(self, chat_id, user_id, content, metadata=None):
        self.private_calls.append(
            {
                "chat_id": chat_id,
                "user_id": user_id,
                "content": content,
                "metadata": metadata,
            }
        )
        return SendResult(success=self.private_success, message_id="ephemeral-1")

    async def send(self, chat_id, content, metadata=None):
        self.public_calls.append(
            {"chat_id": chat_id, "content": content, "metadata": metadata}
        )
        return SendResult(success=True, message_id="public-1")


class _FallbackOnlyAdapter:
    send_private_notice = BasePlatformAdapter.send_private_notice

    def __init__(self):
        self.private_calls = []
        self.public_calls = []

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        self.public_calls.append(
            {
                "chat_id": chat_id,
                "content": content,
                "reply_to": reply_to,
                "metadata": metadata,
            }
        )
        return SendResult(success=True, message_id="public-1")


def _slack_source(*, user_id: str | None = "U_SENDER"):
    return SessionSource(
        platform=Platform.SLACK,
        chat_id="C_TEAM",
        chat_type="group",
        user_id=user_id,
        thread_id="1712345678.000100",
    )


def test_slack_memory_context_boolean_true_resolves_private():
    mode = _resolve_gateway_memory_context_display(
        {"display": {"platforms": {"slack": {"memory_context": True}}}},
        "slack",
        Platform.SLACK,
    )

    assert mode == "private"


def test_slack_memory_context_defaults_off():
    mode = _resolve_gateway_memory_context_display({}, "slack", Platform.SLACK)

    assert mode == "off"


def test_slack_memory_context_private_sends_ephemeral_to_sender():
    adapter = _FakeSlackAdapter()
    metadata = {"thread_id": "1712345678.000100"}

    asyncio.run(
        _send_gateway_memory_context_display(
            adapter,
            _slack_source(),
            "# Hindsight\n- profile:team: public team note",
            mode="private",
            metadata=metadata,
        )
    )

    assert len(adapter.private_calls) == 1
    assert adapter.private_calls[0]["chat_id"] == "C_TEAM"
    assert adapter.private_calls[0]["user_id"] == "U_SENDER"
    assert adapter.private_calls[0]["metadata"] == metadata
    assert "Memory recall context" in adapter.private_calls[0]["content"]
    assert "public team note" in adapter.private_calls[0]["content"]
    assert adapter.public_calls == []


def test_slack_memory_context_private_without_sender_does_not_post_publicly():
    adapter = _FakeSlackAdapter()

    asyncio.run(
        _send_gateway_memory_context_display(
            adapter,
            _slack_source(user_id=None),
            "visible only if private target exists",
            mode="private",
        )
    )

    assert adapter.private_calls == []
    assert adapter.public_calls == []


def test_slack_memory_context_private_does_not_use_base_public_fallback():
    adapter = _FallbackOnlyAdapter()

    asyncio.run(
        _send_gateway_memory_context_display(
            adapter,
            _slack_source(),
            "do not leak this into the channel",
            mode="private",
        )
    )

    assert adapter.private_calls == []
    assert adapter.public_calls == []


def test_slack_memory_context_public_mode_posts_channel_message():
    adapter = _FakeSlackAdapter()

    asyncio.run(
        _send_gateway_memory_context_display(
            adapter,
            _slack_source(),
            "debug context",
            mode="public",
            metadata={"thread_id": "1712345678.000100"},
        )
    )

    assert adapter.private_calls == []
    assert len(adapter.public_calls) == 1
    assert adapter.public_calls[0]["chat_id"] == "C_TEAM"
    assert "debug context" in adapter.public_calls[0]["content"]


def test_memory_context_formatter_truncates_and_neutralizes_fences():
    content = _format_gateway_memory_context(
        "before ```boom\n" + "a" * (_GATEWAY_MEMORY_CONTEXT_MAX_CHARS + 10)
    )

    assert "Memory recall context" in content
    assert "… truncated" in content
    assert "```boom" not in content
