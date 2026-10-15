"""Exact adapter-owned cards retire before I/O; accepted labels survive timer races."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from gateway.config import PlatformConfig
from plugins.platforms.discord.adapter import DiscordAdapter, ExecApprovalView
from tools import approval
from tools.approval_gateway_wait import _await_gateway_decision
from gateway.run_turn_runner_approval_settle import register_timeout_notice


@pytest.mark.asyncio
async def test_local_answer_cannot_be_overwritten_by_timeout(monkeypatch):
    view = ExecApprovalView("route", {"1"}, request_id="exact")
    embed = SimpleNamespace(color=None)
    embed.set_footer = lambda **kw: setattr(embed, "footer", kw["text"])
    view._message = SimpleNamespace(embeds=[embed], edit=AsyncMock())
    interaction = SimpleNamespace(user=SimpleNamespace(id=1, display_name="operator", roles=[]),
        message=view._message, response=SimpleNamespace(edit_message=AsyncMock(), send_message=AsyncMock()))
    monkeypatch.setattr(approval, "resolve_gateway_approval", lambda *a, **kw: 1)
    await view._resolve(interaction, "once", None, "platform.discord.approval.resolved_once")
    footer = embed.footer
    await view.on_timeout()
    assert embed.footer == footer
    view._message.edit.assert_not_awaited()


@pytest.mark.asyncio
async def test_owner_settlement_retires_only_exact_card_before_edit(monkeypatch):
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="synthetic"))
    messages = []
    async def send(**kw):
        message = SimpleNamespace(id=len(messages)+1, embeds=[kw["embed"]], edit=AsyncMock())
        messages.append((message, kw["view"]))
        return message
    channel = SimpleNamespace(send=send)
    adapter._client = SimpleNamespace(get_channel=lambda _: channel)
    for rid in ("A", "B"):
        await adapter.send_exec_approval("555", "inert", "route", metadata={"approval_request_id": rid})
    message, first = messages[0]
    async def edit(**kw):
        assert first.resolved
        assert all(child.disabled for child in first.children)
        assert ("route", "A") not in adapter._exec_approval_views
        raise RuntimeError("synthetic edit failure")
    message.edit.side_effect = edit
    await adapter.retire_exec_approval("route", "A", "resolved")
    assert not messages[1][1].resolved
    footer = str(message.embeds[0].footer)
    await first.on_timeout()
    assert str(message.embeds[0].footer) == footer
    assert "no action taken" not in footer
    await adapter.retire_exec_approval("route", "B", "unknown")


@pytest.mark.asyncio
async def test_settlement_during_send_is_disabled_when_delivery_finishes():
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="synthetic"))
    arrived, release = asyncio.Event(), asyncio.Event()
    sent = []
    async def send(**kw):
        sent.append(kw)
        arrived.set()
        await release.wait()
        return SimpleNamespace(id=1, embeds=[kw["embed"]], edit=AsyncMock())
    adapter._client = SimpleNamespace(get_channel=lambda _: SimpleNamespace(send=send))
    task = asyncio.create_task(adapter.send_exec_approval("555", "inert", "route", metadata={"approval_request_id": "A"}))
    await arrived.wait()
    await adapter.retire_exec_approval("route", "A", "resolved")
    assert sent[0]["view"].resolved
    assert all(child.disabled for child in sent[0]["view"].children)
    release.set()
    assert (await task).success
    view = sent[0]["view"]
    view._message.edit.assert_awaited_once()
    await view.on_timeout()
    view._message.edit.assert_awaited_once()
    assert not adapter._exec_approval_views


@pytest.mark.asyncio
async def test_failed_send_cleans_exact_pending_view():
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="synthetic"))
    views = []
    async def send(**kw):
        views.append(kw["view"])
        raise RuntimeError("synthetic transport failure")
    adapter._client = SimpleNamespace(get_channel=lambda _: SimpleNamespace(send=send))
    result = await adapter.send_exec_approval("555", "inert", "route", metadata={"approval_request_id": "A"})
    assert not result.success
    assert views[0].resolved
    assert all(child.disabled for child in views[0].children)
    assert not adapter._exec_approval_views


def test_real_waiter_host_callback_retires_peer_answer(monkeypatch):
    from gateway.run_turn_runner import TurnRunner
    from tools import approval_gateway_wait as wait
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="synthetic"))
    sent = []
    async def send(**kw):
        message = SimpleNamespace(id=1, embeds=[kw["embed"]], edit=AsyncMock())
        sent.append((message, kw["view"]))
        return message
    adapter._client = SimpleNamespace(get_channel=lambda _: SimpleNamespace(send=send))
    runner = object.__new__(TurnRunner)
    runner._ctx = SimpleNamespace(_status_adapter=adapter, _status_chat_id="555", _status_thread_metadata={},
        session_key="synthetic-peer-host", _run_still_current=lambda: True)
    runner._close_native_stream_boundary = lambda _: None
    def schedule(coro, label):
        result = asyncio.run(coro)
        return SimpleNamespace(result=lambda timeout=None: result)
    runner._schedule = schedule
    def peer_wins(event, key, **kw):
        row = approval.list_gateway_approvals(key)[0]
        assert approval.resolve_gateway_approval(key, "once", request_id=row["request_id"]) == 1
        return "timeout"  # committed decision wins the deadline race
    monkeypatch.setattr(wait, "_poll_event", peer_wins)
    result = wait._await_gateway_decision("synthetic-peer-host", runner._approval_notify_sync, {"command": "inert"})
    assert result["resolved"] and result["choice"] == "once"
    assert sent[0][1].resolved
    assert not adapter._exec_approval_views
    footer = str(sent[0][0].embeds[0].footer)
    assert "execution is not confirmed" in footer
    asyncio.run(sent[0][1].on_timeout())
    assert str(sent[0][0].embeds[0].footer) == footer


@pytest.mark.asyncio
async def test_disconnect_stops_and_detaches_owned_views():
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="synthetic"))
    sent = []
    async def send(**kw):
        sent.append(kw["view"])
        return SimpleNamespace(id=1)
    adapter._client = SimpleNamespace(get_channel=lambda _: SimpleNamespace(send=send), close=AsyncMock())
    await adapter.send_exec_approval("555", "inert", "route", metadata={"approval_request_id": "A"})
    await adapter.disconnect()
    assert sent[0].resolved and sent[0].is_finished()
    assert all(child.disabled for child in sent[0].children)
    assert not adapter._exec_approval_views


@pytest.mark.asyncio
async def test_ambiguous_send_settled_before_ack_never_leaves_live_controls(monkeypatch):
    from gateway.run_turn_runner import TurnRunner
    from tools import approval_gateway_wait as wait
    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="synthetic"))
    arrived, release, edited = asyncio.Event(), asyncio.Event(), asyncio.Event()
    sent = []
    async def edit(**kw):
        edited.set()
    async def send(**kw):
        sent.append(kw["view"])
        arrived.set()
        await release.wait()
        return SimpleNamespace(id=1, embeds=[kw["embed"]], edit=AsyncMock(side_effect=edit))
    adapter._client = SimpleNamespace(get_channel=lambda _: SimpleNamespace(send=send))
    runner = object.__new__(TurnRunner)
    runner._ctx = SimpleNamespace(_status_adapter=adapter, _status_chat_id="555", _status_thread_metadata={},
        session_key="synthetic-ambiguous", _run_still_current=lambda: True)
    runner._close_native_stream_boundary = lambda _: None
    from concurrent.futures import Future
    scheduled = []
    def schedule(coro, label):
        future = Future()
        scheduled.append((coro, future))
        return future
    runner._schedule = schedule
    monkeypatch.setattr("gateway.run._approval_send_outcome", lambda *a, **k: "ambiguous")
    monkeypatch.setattr(wait, "_poll_event", lambda *a, **k: "timeout")
    result = wait._await_gateway_decision("synthetic-ambiguous", runner._approval_notify_sync, {"command": "inert"})
    assert not result["resolved"]
    release.set()
    # Deterministically deliver the acknowledgement after host timeout. The
    # real callback registers against the gone exact entry and retires unknown.
    for coro, future in scheduled:
        future.set_result(await coro)
    assert edited.is_set()
    assert len(sent) == 1
    assert sent[0].resolved and sent[0].is_finished()
    assert all(child.disabled for child in sent[0].children)
    assert not adapter._exec_approval_views
