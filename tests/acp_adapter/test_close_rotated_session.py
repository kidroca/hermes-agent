"""ACP close preserves compression lineage and releases stable task resources."""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acp_adapter.server import HermesACPAgent
from acp_adapter.session import SessionManager
from hermes_state import SessionDB


@pytest.mark.asyncio
@pytest.mark.parametrize("rotated", [False, True])
async def test_close_ends_runtime_head_and_releases_each_resource_identity(tmp_path, monkeypatch, rotated):
    import run_agent
    from tools.computer_use import tool as computer_use
    from tools.terminal_tool import _task_env_overrides

    db = SessionDB(tmp_path / "state.db")
    memory = MagicMock()
    runtime = SimpleNamespace(
        model="test", _session_db=db, _session_db_created=True,
        _owns_session_db=False, _end_session_on_close=True,
        _memory_manager=memory, _memory_provider_shutdown=False,
        _session_messages=[], client=None, _process_owner_task_ids=set(),
        _close_active_children=MagicMock(), _close_request_clients=MagicMock(),
        _close_codex_session=MagicMock(), _trim_process_memory=MagicMock(), interrupt=MagicMock(),
    )
    for name in ("close", "shutdown_memory_provider", "_close_task_resources",
                 "_drop_shared_client", "_finalize_owned_session_row"):
        setattr(runtime, name, getattr(run_agent.AIAgent, name).__get__(runtime))
    manager = SessionManager(agent_factory=lambda: runtime, db=db)
    server = HermesACPAgent(session_manager=manager)
    state = manager.create_session(cwd=str(tmp_path))
    sid = state.session_id
    head = sid + "-head" if rotated else sid
    runtime.session_id = head
    db.create_session(sid, source="acp")
    db.append_message(sid, "user", "original")
    db.append_message(sid, "assistant", "original reply")
    if rotated:
        db.end_session(sid, "compression")
        db.create_session(head, source="acp", parent_session_id=sid)
        db.append_message(head, "user", "live summary")
    state.history = [{"role": "user", "content": "must not replace parent"}]
    # Resources really held under the stable task key; no external backends.
    resources = {kind: {sid: object()} for kind in ("vm", "browser", "computer")}
    released = {kind: [] for kind in resources}

    def cleanup(kind):
        def release(task_id):
            released[kind].append(task_id)
            resources[kind].pop(task_id, None)
        return release

    monkeypatch.setattr(run_agent, "cleanup_vm", cleanup("vm"))
    monkeypatch.setattr(run_agent, "cleanup_browser", cleanup("browser"))
    monkeypatch.setattr(computer_use, "release_computer_use_session", cleanup("computer"))
    try:
        parent_before = db.get_session(sid)
        messages_before = {key: db.get_messages(key, include_inactive=True) for key in {sid, head}}
        await asyncio.wait_for(asyncio.gather(server.close_session(sid), server.close_session(sid)), 3)
        await server.close_session(sid)
        assert db.get_session(head)["end_reason"] == "acp_close"
        assert db.get_session(head)["ended_at"] is not None
        if rotated:
            parent_after = db.get_session(sid)
            assert parent_after["end_reason"] == parent_before["end_reason"] == "compression"
            assert parent_after["ended_at"] == parent_before["ended_at"]
            assert db.get_session(head)["parent_session_id"] == sid
        for key, messages in messages_before.items():
            assert db.get_messages(key, include_inactive=True) == messages
        for kind in resources:
            assert not resources[kind]
            assert released[kind].count(sid) == 1
            assert set(released[kind]) == {sid, head}
            assert len(released[kind]) == len({sid, head})
        assert sid not in _task_env_overrides
        memory.on_session_end.assert_called_once_with(state.history)
        memory.shutdown_all.assert_called_once()
        db.create_session("sibling", source="acp")
        assert db.get_session("sibling") is not None
    finally:
        db.close()
