"""A recovered submit store must also reach the already-built turn agent."""
import sqlite3
import threading
from types import SimpleNamespace

import pytest

from agent.session_persistence import SessionPersistenceMixin
import hermes_state_registry as registry
from tui_gateway import server


class OfflineAgent(SessionPersistenceMixin):
    def __init__(self, db, key):
        self._session_db = db
        self._owns_session_db = False
        self._session_db_created = True
        self.session_id = key

    def run_conversation(self, message):
        messages = [{"role": "user", "content": message},
                    {"role": "assistant", "content": "offline response"}]
        self._flush_messages_to_session_db_unlocked(messages, [])
        return messages


@pytest.mark.parametrize("profile", [False, True])
def test_submit_recovery_reaches_prepared_turn(tmp_path, monkeypatch, profile):
    launch = tmp_path / "launch"
    launch.mkdir()
    home = tmp_path / "profile" if profile else launch
    home.mkdir(exist_ok=True)
    monkeypatch.setattr(server, "_hermes_home", str(launch))
    monkeypatch.setattr(server, "_db", None)
    monkeypatch.setattr(server, "_db_error", None)
    opener = registry._open_session_db
    def fail(path):
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(registry, "_open_session_db", fail)
    assert server._get_db() is None
    if profile:
        with pytest.raises(RuntimeError, match="profile session store unavailable"):
            server._open_profile_session_db(home)
    agent = OfflineAgent(None, "recover")
    monkeypatch.setattr(registry, "_open_session_db", opener)
    initial_agent = OfflineAgent(None, "recover")
    session = {"session_key": "recover", "agent": initial_agent, "history": [],
               "history_lock": threading.Lock(), "cwd": str(tmp_path),
               "profile_home": str(home) if profile else None}
    monkeypatch.setattr(server, "_resolve_model", lambda: "offline")
    monkeypatch.setattr(server, "_load_cfg", lambda: {})
    assert server._persist_session_row_for_submit("request", session) is None
    # Keep the real preparation path; isolate network/runtime peripheral hooks.
    for name in ("_wire_callbacks", "_apply_pending_model_switch", "_sync_agent_model_with_config",
                 "_sync_agent_compression_with_config", "_sync_agent_fallback_with_config", "_register_session_cwd"):
        monkeypatch.setattr(server, name, lambda *a: None)
    # Capability synchronization may replace the agent after model synchronization.
    monkeypatch.setattr(server, "_sync_bot_capabilities", lambda sid, current: current.update(agent=agent))
    monkeypatch.setattr(server, "_set_session_context", lambda *a, **kw: [])
    monkeypatch.setattr(server, "_profile_runtime_scope_tokens", lambda *a: None)
    monkeypatch.setattr(server, "_start_turn_voice", lambda: (None, False))
    monkeypatch.setattr(server, "_pending_reaction_notes", lambda *a: "")
    monkeypatch.setattr(server, "_hud_surface_note", lambda *a: "")
    monkeypatch.setattr(server, "make_stream_renderer", lambda *a: None)
    events = []
    monkeypatch.setattr(server, "_emit", lambda *a: events.append(a))
    st = server._TurnRun(agent=SimpleNamespace(), one_turn_restore=None,
                         terminal_callback=None, receipt_committed=False)
    try:
        prepared = server._prepare_turn_input("sid", session, st, "hello", [])
        assert prepared is not None
        assert st.agent is agent
        assert initial_agent._session_db is None
        assert agent._session_db is not None
        db = agent._session_db
        assert agent._owns_session_db is profile
        assert db.db_path == home / "state.db"
        messages = agent.run_conversation(prepared[1])
        assert [(m["role"], m["content"]) for m in db.get_messages("recover")] == [
            (m["role"], m["content"]) for m in messages]
        generation = registry._generations[(home / "state.db").resolve()]
        refs = generation.refcount
        server._prepare_turn_input("sid", session, st, "again", [])
        assert agent._session_db is db
        assert generation.refcount == refs == 1
        assert not events
        from run_agent import AIAgent
        agent._end_session_on_close = False
        AIAgent._finalize_owned_session_row(agent)
        AIAgent._finalize_owned_session_row(agent)
        if profile:
            assert not agent._owns_session_db
            assert (home / "state.db").resolve() not in registry._generations
        else:
            assert db is server._get_db()
            assert db.get_session("recover") is not None
        agent._session_db = None
        if profile:
            monkeypatch.setattr(registry, "_open_session_db", fail)
            with pytest.raises(RuntimeError, match="profile session store unavailable"):
                server._prepare_turn_input("sid", session, st, "not admitted", [])
            assert not events  # fail-closed errors do not get a duplicate warning
        else:
            monkeypatch.setattr(server, "_get_db", lambda: None)
            assert server._prepare_turn_input("sid", session, st, "live only", []) is not None
            assert events == [("status.update", "sid", {
                "kind": "warning", "text": "Session storage is unavailable; this turn may not be saved."})]
    finally:
        from tools.approval_context import reset_current_session_key
        reset_current_session_key(st.scopes.approval)
        registry.close_all_under(tmp_path)
