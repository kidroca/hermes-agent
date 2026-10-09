"""Close/load ordering and cleanup ownership survive ACP runtime handoffs."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acp_adapter.server import HermesACPAgent
from acp_adapter.session import SessionManager
from hermes_state import SessionDB


def _runtime():
    return SimpleNamespace(
        model="test", provider="openrouter", interrupt=MagicMock(),
        shutdown_memory_provider=MagicMock(), close=MagicMock(),
    )


def test_reopen_cannot_interleave_close_publication(tmp_path, monkeypatch):
    from tools.terminal_tool import _task_env_overrides

    with SessionDB(tmp_path / "state.db") as db, ThreadPoolExecutor(max_workers=2) as pool:
        manager = SessionManager(agent_factory=_runtime, db=db)
        state = manager.create_session(cwd=str(tmp_path))
        state.history = [{"role": "user", "content": "retained"}]
        manager.save_session(state.session_id)
        manager.begin_close(state.session_id)
        publishing, attempted, restored = threading.Event(), threading.Event(), threading.Event()
        underlying = manager._restore_lock
        blocked = []

        class ObservedRestoreLock:
            def __enter__(self):
                acquired = underlying.acquire(blocking=False)
                if threading.current_thread().name.startswith("reopen"):
                    blocked.append(not acquired)
                    attempted.set()
                if not acquired:
                    underlying.acquire()
                return self

            def __exit__(self, *_args):
                underlying.release()

        monkeypatch.setattr(manager, "_restore_lock", ObservedRestoreLock())
        remember = manager._remember_closed

        def publish(session_id):
            publishing.set()
            assert attempted.wait(5)
            # If close doesn't own the restore boundary, deterministically let the
            # explicit load finish first: the subsequent tombstone would hide it.
            if not blocked[0]:
                assert restored.wait(5)
            remember(session_id)

        monkeypatch.setattr(manager, "_remember_closed", publish)
        closing = pool.submit(manager.finish_close, state)
        assert publishing.wait(5)
        loaded = []

        def reopen():
            try:
                loaded.append(manager.update_cwd(state.session_id, str(tmp_path / "new"), reopen=True))
            finally:
                restored.set()

        thread = threading.Thread(target=reopen, name="reopen-session")
        thread.start()
        try:
            closing.result(timeout=5)
            thread.join(timeout=5)
            assert not thread.is_alive()
            assert loaded and loaded[0] is not None
            assert manager.get_session(state.session_id) is loaded[0]
            assert not manager.is_closed(state.session_id)
            assert _task_env_overrides[state.session_id]["cwd"] == str(tmp_path / "new")
        finally:
            thread.join(timeout=5)


@pytest.mark.asyncio
async def test_close_interrupts_detached_delegation_without_touching_sibling(tmp_path):
    from tools import async_delegation

    released, started, finished = threading.Event(), threading.Event(), threading.Event()
    sibling_interrupt = MagicMock()

    def runner():
        started.set()
        try:
            assert released.wait(5)
            return {"summary": "interrupted"}
        finally:
            finished.set()

    with SessionDB(tmp_path / "state.db") as db:
        manager = SessionManager(agent_factory=_runtime, db=db)
        server = HermesACPAgent(session_manager=manager)
        state = manager.create_session()
        state.agent.session_id = state.session_id
        handle = async_delegation.dispatch_async_delegation(
            goal="blocked child", context=None, toolsets=None, role="leaf", model=None,
            session_key="acp-test", parent_session_id=state.session_id,
            runner=runner, interrupt_fn=released.set,
        )
        assert handle["status"] == "dispatched"
        # A registry sibling proves the close selector cannot cancel other sessions.
        with async_delegation._records_lock:
            async_delegation._records["test-sibling"] = {
                "status": "running", "parent_session_id": "other-session",
                "interrupt_fn": sibling_interrupt,
            }
        try:
            assert await asyncio.to_thread(started.wait, 3)
            await asyncio.wait_for(server.close_session(state.session_id), 3)
            assert released.is_set()
            assert await asyncio.to_thread(finished.wait, 3)
            sibling_interrupt.assert_not_called()
        finally:
            released.set()
            await asyncio.to_thread(finished.wait, 5)
            with async_delegation._records_lock:
                async_delegation._records.pop("test-sibling", None)


@pytest.mark.asyncio
async def test_switch_transfers_process_ownership_before_close(tmp_path, monkeypatch):
    from run_agent import AIAgent
    from tools.process_registry import process_registry
    import hermes_cli.model_switch as model_switch

    runtimes = []

    def factory():
        agent = _runtime()
        agent._process_owner_task_ids = set()
        agent._close_task_resources = AIAgent._close_task_resources.__get__(agent)

        def close(*, preserve_session=False):
            if not preserve_session:
                agent._close_task_resources(agent.session_id)

        agent.close = close
        runtimes.append(agent)
        return agent

    monkeypatch.setattr(model_switch, "switch_model", lambda **_kw: SimpleNamespace(
        success=True, target_provider="openrouter", new_model="replacement",
    ))
    processes = [
        {"session_id": "owned", "owner_task_id": "old-task", "status": "running"},
        {"session_id": "sibling", "owner_task_id": "foreign", "status": "running"},
        {"session_id": "persistent", "owner_task_id": "old-task", "status": "running", "persist_on_release": True},
    ]
    monkeypatch.setattr(process_registry, "list_sessions", lambda: processes)
    killed = MagicMock()
    monkeypatch.setattr(process_registry, "kill_process", killed)
    for name in ("cleanup_vm", "cleanup_browser"):
        monkeypatch.setattr(f"run_agent.{name}", MagicMock())
    with SessionDB(tmp_path / "state.db") as db:
        manager = SessionManager(agent_factory=factory, db=db)
        server = HermesACPAgent(session_manager=manager)
        state = manager.create_session()
        state.agent.session_id = state.session_id
        state.agent._process_owner_task_ids.add("old-task")
        server._switch_model(state, "replacement")
        state.agent.session_id = state.session_id
        killed.assert_not_called()
        await server.close_session(state.session_id)
        killed.assert_called_once_with("owned", source="agent_close", consume_output=True)
        assert runtimes[-1]._process_owner_task_ids == {"old-task"}
