"""Close drains detached RPC work and preserves shared DB ownership."""

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from acp.schema import CloseSessionResponse, TextContentBlock

from acp_adapter.server import HermesACPAgent
from acp_adapter.session import SessionManager
from hermes_state import SessionDB


def _runtime(**extra):
    return SimpleNamespace(
        model="test",
        interrupt=MagicMock(),
        shutdown_memory_provider=MagicMock(),
        close=MagicMock(),
        **extra,
    )


@pytest.mark.asyncio
async def test_close_capability_provisional_and_explicit_reopen(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    runtimes = []

    def factory():
        runtime = _runtime()
        runtimes.append(runtime)
        return runtime

    manager = SessionManager(agent_factory=factory, db=db)
    server = HermesACPAgent(session_manager=manager)
    try:
        capabilities = (
            await asyncio.wait_for(server.initialize(protocol_version=1), timeout=3)
        ).agent_capabilities
        wire = capabilities.model_dump(by_alias=True, exclude_none=True)
        assert wire["sessionCapabilities"]["close"] == {}

        provisional = await asyncio.wait_for(server.new_session(cwd=str(tmp_path)), timeout=3)
        assert isinstance(
            await asyncio.wait_for(server.close_session(provisional.session_id), timeout=3),
            CloseSessionResponse,
        )
        assert db.get_session(provisional.session_id) is None

        created = await asyncio.wait_for(server.new_session(cwd=str(tmp_path)), timeout=3)
        state = manager.get_session(created.session_id)
        state.history = [{"role": "user", "content": "keep this history"}]
        manager.save_session(created.session_id)
        assert isinstance(
            await asyncio.wait_for(server.close_session(created.session_id), timeout=3),
            CloseSessionResponse,
        )
        row = db.get_session(created.session_id)
        assert row["end_reason"] == "acp_close" and row["ended_at"] is not None
        assert db.get_messages_as_conversation(created.session_id)[0]["content"] == "keep this history"

        refused = await server.prompt(
            [TextContentBlock(type="text", text="do not resurrect")], created.session_id
        )
        assert refused.stop_reason == "refusal"
        assert manager.get_session(created.session_id) is None

        loaded = await asyncio.wait_for(
            server.load_session(cwd="/restored", session_id=created.session_id), timeout=3
        )
        assert loaded is not None
        reopened = db.get_session(created.session_id)
        assert reopened["ended_at"] is None and reopened["end_reason"] is None
        restored = manager.get_session(created.session_id)
        assert restored.agent is runtimes[-1]
        assert restored.cwd == "/restored"
        assert restored.history[0]["content"] == "keep this history"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_close_cancels_and_drains_active_prompt_before_cleanup(tmp_path):
    started = threading.Event()
    release = threading.Event()
    order = []

    def run_conversation(**kwargs):
        started.set()
        assert release.wait(5)
        order.append("drained")
        return {"messages": [{"role": "user", "content": "accepted"}], "interrupted": True}

    def interrupt():
        order.append("interrupt")
        release.set()

    runtime = SimpleNamespace(
        model="test", run_conversation=run_conversation,
        hard_interrupt=interrupt, interrupt=interrupt,
        shutdown_memory_provider=MagicMock(), close=lambda: order.append("closed"),
    )
    db = SessionDB(tmp_path / "state.db")
    manager = SessionManager(agent_factory=lambda: runtime, db=db)
    server = HermesACPAgent(session_manager=manager)
    state = manager.create_session()
    sid = state.session_id
    caller = asyncio.create_task(server.prompt([TextContentBlock(type="text", text="accepted")], sid))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        state.queued_prompts.append("discard this")
        assert isinstance(
            await asyncio.wait_for(server.close_session(sid), timeout=3),
            CloseSessionResponse,
        )
        prompt_response = await caller
        assert prompt_response.stop_reason == "cancelled"
        assert state.closing and state.cancel_event.is_set() and state.queued_prompts == []
        assert order == ["interrupt", "drained", "closed"]
        assert not server._active_prompt_tasks and not server._close_tasks
        assert db.get_session(sid)["end_reason"] == "acp_close"
        assert db.get_messages_as_conversation(sid)[0]["content"] == "accepted"
        runtime.shutdown_memory_provider.assert_called_once()
        assert await server.close_session("never-created") is None
    finally:
        release.set()
        await asyncio.gather(*server._active_prompt_tasks.get(sid, ()), return_exceptions=True)
        db.close()


@pytest.mark.asyncio
async def test_close_shared_db_restore_rollback_and_bounded_tombstones(tmp_path, monkeypatch):
    from run_agent import AIAgent
    from tools.terminal_tool import _task_env_overrides

    db = SessionDB(tmp_path / "state.db")
    memory, client = MagicMock(), MagicMock()
    runtime = SimpleNamespace(
        model="test", _session_db=db, _session_db_created=True,
        _owns_session_db=False, _end_session_on_close=True,
        _memory_manager=memory, _memory_provider_shutdown=False,
        _session_messages=[], client=client,
        _close_task_resources=MagicMock(), _close_active_children=MagicMock(),
        _close_openai_client=MagicMock(), _close_request_clients=MagicMock(),
        _close_codex_session=MagicMock(), _trim_process_memory=MagicMock(), interrupt=MagicMock(),
    )
    # Real ownership/close phases, without provider/network initialization.
    for name in ("close", "shutdown_memory_provider", "_drop_shared_client", "_finalize_owned_session_row"):
        setattr(runtime, name, getattr(AIAgent, name).__get__(runtime))
    manager = SessionManager(agent_factory=lambda: runtime, db=db)
    server = HermesACPAgent(session_manager=manager)
    state = manager.create_session(cwd=str(tmp_path))
    sid = state.session_id
    runtime.session_id = sid
    db.create_session(sid, source="acp")
    db.append_message(sid, "user", "archived original")
    db.append_message(sid, "assistant", "original reply")
    db.archive_and_compact(sid, [{"role": "user", "content": "live summary"}])
    state.history = [{"role": "user", "content": "must not replace canonical rows"}]
    try:
        before = db.get_messages(sid, include_inactive=True)
        await server.close_session(sid)
        await server.close_session(sid)
        assert db.get_messages(sid, include_inactive=True) == before
        assert db.get_session(sid)["end_reason"] == "acp_close"
        assert sid not in _task_env_overrides
        memory.on_session_end.assert_called_once_with(state.history)
        memory.shutdown_all.assert_called_once()
        runtime._close_task_resources.assert_called_once_with(sid)
        runtime._close_openai_client.assert_called_once_with(client, reason="agent_close", shared=True)
        db.create_session("sibling", source="acp")
        db.append_message("sibling", "user", "still writable")
        assert db.get_messages_as_conversation("sibling")[0]["content"] == "still writable"

        def failed_factory():
            raise RuntimeError("provider unavailable")

        # Failed history hydration must not reopen the row or replace it with [].
        with monkeypatch.context() as failed_read:
            failed_read.setattr(db, "get_messages_as_conversation", MagicMock(side_effect=RuntimeError("read failed")))
            assert manager.update_cwd(sid, ".", reopen=True) is None
        assert db.get_session(sid)["end_reason"] == "acp_close"
        assert db.get_messages(sid, include_inactive=True) == before

        monkeypatch.setattr(manager, "_agent_factory", failed_factory)
        assert manager.update_cwd(sid, ".", reopen=True) is None
        assert db.get_session(sid)["end_reason"] == "acp_close"
        assert db.get_session(sid)["ended_at"] is not None
        assert manager.get_session(sid) is None and manager.is_closed(sid)
        assert db.get_messages(sid, include_inactive=True) == before
        for index in range(manager._CLOSED_TOMBSTONE_LIMIT + 1):
            manager._remember_closed(f"provisional-{index}")
        assert len(manager._closed_session_ids) == manager._CLOSED_TOMBSTONE_LIMIT
        assert len(manager._closed_session_order) == manager._CLOSED_TOMBSTONE_LIMIT
        assert not manager.is_closed("provisional-0")
        assert manager.is_closed(sid)
        assert manager.get_session(sid) is None
    finally:
        db.close()
