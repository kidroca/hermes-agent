"""Accepted model RPC work outlives its caller, but never session close."""

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from acp.schema import CloseSessionResponse, TextContentBlock

from acp_adapter.server import HermesACPAgent
from acp_adapter.session import SessionManager
from hermes_state import SessionDB


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel_caller", [False, True])
async def test_close_drains_model_worker_and_rejects_late_claims(tmp_path, monkeypatch, cancel_caller):
    import hermes_cli.model_switch as model_switch

    started, release, finished = threading.Event(), threading.Event(), threading.Event()
    interrupted = asyncio.Event()
    runtimes = []
    loop = asyncio.get_running_loop()

    def factory():
        runtime = SimpleNamespace(
            model="test", provider="openrouter", interrupt=MagicMock(),
            shutdown_memory_provider=MagicMock(), close=MagicMock(),
        )
        runtime.interrupt.side_effect = lambda: loop.call_soon_threadsafe(interrupted.set)
        runtimes.append(runtime)
        return runtime

    def resolve(**kwargs):
        started.set()
        assert release.wait(10)
        return SimpleNamespace(success=True, target_provider="openrouter", new_model="new-model")

    monkeypatch.setattr(model_switch, "switch_model", resolve)
    db = SessionDB(tmp_path / "state.db")
    manager = SessionManager(agent_factory=factory, db=db)
    server = HermesACPAgent(session_manager=manager)
    state = manager.create_session()
    original_switch = server._switch_model

    def switch(*args, **kwargs):
        try:
            return original_switch(*args, **kwargs)
        finally:
            finished.set()

    monkeypatch.setattr(server, "_switch_model", switch)
    caller = asyncio.create_task(server.set_session_model("new-model", state.session_id))
    closes = []
    try:
        assert await asyncio.to_thread(started.wait, 3)
        if cancel_caller:
            caller.cancel()
            with pytest.raises(asyncio.CancelledError):
                await caller
        # Even a disconnected caller must retain upstream busy admission until
        # the owned model worker exits; no competing rebuild may enter.
        from acp.exceptions import RequestError

        assert state.command_op is True
        with pytest.raises(RequestError, match="busy"):
            await asyncio.wait_for(server.set_session_model("competing", state.session_id), 3)
        assert server._active_model_tasks[state.session_id]
        closes = [asyncio.create_task(server.close_session(state.session_id)) for _ in range(2)]
        await asyncio.wait_for(interrupted.wait(), 3)
        # A late claim must be rejected without entering the blocked resolver.
        assert await asyncio.wait_for(server.set_session_model("late", state.session_id), 3) is None
        refused = await server.prompt([TextContentBlock(type="text", text="late")], state.session_id)
        assert refused.stop_reason == "refusal"
        assert all(not task.done() for task in closes)
        runtimes[0].close.assert_not_called()
        release.set()
        assert all(isinstance(result, CloseSessionResponse) for result in await asyncio.wait_for(
            asyncio.gather(*closes), 3
        ))
        assert finished.is_set()
        assert len(runtimes) == 2
        runtimes[-1].close.assert_called_once()
        runtimes[-1].shutdown_memory_provider.assert_called_once()
        assert manager.get_session(state.session_id) is None
        assert not server._close_tasks
        if not cancel_caller:
            assert await caller is not None
    finally:
        release.set()
        await asyncio.to_thread(finished.wait, 3)
        await asyncio.gather(caller, *closes, return_exceptions=True)
        db.close()
