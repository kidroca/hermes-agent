"""Host-owned settlement and late send receipts never guess an answer."""
from concurrent.futures import Future
from types import SimpleNamespace
from gateway.run_turn_runner_approval_settle import register_timeout_notice, register_after_ambiguous_send


def test_registration_loss_retires_unknown_and_callback_is_exact(monkeypatch):
    calls = []
    class Adapter:
        async def retire_exec_approval(self, session_key, request_id, reason):
            calls.append((session_key, request_id, reason))
    import asyncio
    runner = SimpleNamespace(_ctx=SimpleNamespace(session_key="route", _status_adapter=Adapter()),
        _schedule=lambda coro, label: asyncio.run(coro))
    monkeypatch.setattr("tools.approval.register_gateway_settle", lambda *args: False)
    register_timeout_notice(runner, {"request_id": "A"}, command="inert", card_message_id="card")
    assert calls == [("route", "A", "unknown")]


def test_ambiguous_ack_uses_captured_scope_and_failed_ack_is_inert(monkeypatch):
    from contextvars import ContextVar
    owner = ContextVar("synthetic-owner", default="unbound")
    calls = []
    monkeypatch.setattr("gateway.run_turn_runner_approval_settle.register_timeout_notice",
        lambda runner, data, **kw: calls.append((owner.get(), data["request_id"], kw["card_message_id"])))
    owner.set("alpha")
    future = Future()
    register_after_ambiguous_send(None, {"request_id": "A"}, command="inert", future=future)
    owner.set("beta")
    future.set_result(SimpleNamespace(success=True, message_id="exact-card"))
    assert calls == [("alpha", "A", "exact-card")]
    failed = Future()
    register_after_ambiguous_send(None, {"request_id": "B"}, command="inert", future=failed)
    failed.set_exception(RuntimeError("synthetic"))
    assert len(calls) == 1
