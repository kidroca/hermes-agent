"""Discord cards resolve their own queue entry, never a later FIFO approval."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from gateway.config import PlatformConfig
from gateway.platforms.base import SendResult
from gateway.run_turn_runner import TurnRunner
from agent.i18n import t
from plugins.platforms.discord import adapter as discord_adapter
from plugins.platforms.discord.adapter import DiscordAdapter
from tools import approval
from tools.approval_gateway_wait import _ApprovalEntry, _await_gateway_decision

SESSION = "agent:main:discord:dm:555"
CHOICES = ["once", "session", "always", "deny"]


@pytest.fixture
def cards(monkeypatch):
    # The shared Discord stub omits the color used by the existing expired-card path.
    monkeypatch.setattr(discord_adapter.discord.Color, "dark_grey", lambda: 0x607D8B, raising=False)
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="***"))
    adapter._allowed_user_ids = {"111"}
    sent = []

    async def send(**kwargs):
        sent.append(kwargs)
        return SimpleNamespace(id=len(sent))

    channel = SimpleNamespace(send=AsyncMock(side_effect=send))
    adapter._client = SimpleNamespace(get_channel=lambda _: channel, fetch_channel=AsyncMock())
    adapter.edit_message = AsyncMock(return_value=SendResult(success=True))
    metadata = {"thread_id": "555", "approval_request_id": "untrusted-old-id"}
    runner = object.__new__(TurnRunner)
    runner._ctx = SimpleNamespace(
        _status_adapter=adapter, _status_chat_id="555", _status_thread_metadata=metadata,
        session_key=SESSION, source=SimpleNamespace(chat_id="555", platform="discord"),
    )

    def schedule(coro, _):
        result = asyncio.run(coro)
        return SimpleNamespace(result=lambda timeout=None: result)

    runner._schedule = schedule
    runner._close_native_stream_boundary = lambda _: None
    monkeypatch.setitem(approval._gateway_queues, SESSION, [])
    yield adapter, runner, sent, metadata
    with approval._lock:
        approval._gateway_queues.pop(SESSION, None)


def _enqueue(command):
    entry = _ApprovalEntry({"command": command})
    with approval._lock:
        approval._gateway_queues.setdefault(SESSION, []).append(entry)
    return entry


def _interaction(user_id=111):
    embed = SimpleNamespace(color=None)
    embed.set_footer = lambda *, text: setattr(embed, "footer", text)
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id, display_name="operator", roles=[]),
        response=SimpleNamespace(send_message=AsyncMock(), edit_message=AsyncMock()),
        message=SimpleNamespace(embeds=[embed]), channel_id=555,
    )


async def _click(view, choice, user_id=111):
    interaction = _interaction(user_id)
    await view._resolve(interaction, choice, None, f"platform.discord.approval.resolved_{choice}")
    return interaction


@pytest.mark.parametrize("choice", CHOICES)
@pytest.mark.parametrize("settlement", ["settled", "expired"])
def test_stale_card_cannot_answer_later_request(cards, monkeypatch, choice, settlement):
    _, runner, sent, _ = cards
    if settlement == "expired":
        # The real wait publishes a generated queue ID, then removes it on timeout.
        monkeypatch.setattr("tools.approval_gateway_wait._poll_event", lambda *a, **k: "timeout")
        result = _await_gateway_decision(SESSION, runner._approval_notify_sync, {"command": "old"})
        assert result["resolved"] is False
    else:
        old = _enqueue("old")
        runner._approval_notify_sync(dict(old.data))
        assert approval.resolve_gateway_approval(SESSION, "deny", request_id=old.data["request_id"]) == 1
    stale_view = sent[0]["view"]
    assert stale_view.resolved is False
    later = _enqueue("later")
    runner._approval_notify_sync(dict(later.data))

    interaction = asyncio.run(_click(stale_view, choice))

    assert later.result is None
    assert not later.event.is_set()
    assert approval._gateway_queues[SESSION] == [later]
    assert interaction.message.embeds[0].footer == t("platform.discord.approval.expired")


@pytest.mark.parametrize("choice", CHOICES)
def test_parallel_cards_route_exactly_and_first_answer_wins(cards, choice):
    _, runner, sent, metadata = cards
    first, second = _enqueue("first"), _enqueue("second")
    for entry in (first, second):
        runner._approval_notify_sync(dict(entry.data))
    assert metadata == {"thread_id": "555", "approval_request_id": "untrusted-old-id"}

    asyncio.run(_click(sent[1]["view"], choice))
    assert second.result == choice and second.event.is_set()
    assert first.result is None and not first.event.is_set()
    assert approval._gateway_queues[SESSION] == [first]
    asyncio.run(_click(sent[1]["view"], "deny"))
    assert second.result == choice and first.result is None
    asyncio.run(_click(sent[0]["view"], "once"))
    assert first.result == "once"
    assert SESSION not in approval._gateway_queues


@pytest.mark.parametrize("request_id", [None, "", "unknown"])
@pytest.mark.parametrize("choice", CHOICES)
def test_missing_or_unknown_card_id_fails_closed(cards, request_id, choice):
    adapter, _, sent, _ = cards
    pending = _enqueue("pending")
    metadata = {} if request_id is None else {"approval_request_id": request_id}
    asyncio.run(adapter.send_exec_approval("555", "pending", SESSION, metadata=metadata))
    # Mutating shared prompt metadata after sending cannot retarget the existing view.
    metadata["approval_request_id"] = pending.data["request_id"]
    interaction = asyncio.run(_click(sent[0]["view"], choice))
    assert pending.result is None and not pending.event.is_set()
    assert interaction.message.embeds[0].footer == t("platform.discord.approval.expired")


@pytest.mark.parametrize("choice", CHOICES)
@pytest.mark.parametrize("user_id,require_admin,admins", [
    (999, False, []), (111, True, [222]), (111, True, []), (111, True, [111]),
])
def test_exact_card_preserves_user_and_admin_gates(cards, choice, user_id, require_admin, admins):
    adapter, runner, sent, _ = cards
    adapter.config.extra = {"require_admin_for_exec_approval": require_admin, "allow_admin_from": admins}
    entry = _enqueue("pending")
    runner._approval_notify_sync(dict(entry.data))
    interaction = asyncio.run(_click(sent[0]["view"], choice, user_id))
    if user_id == 111 and admins == [111]:
        assert entry.result == choice and entry.event.is_set()
    else:
        assert entry.result is None and not entry.event.is_set()
        assert sent[0]["view"].resolved is False
        interaction.response.send_message.assert_awaited_once()
        interaction.response.edit_message.assert_not_called()
