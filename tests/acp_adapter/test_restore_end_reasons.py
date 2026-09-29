"""Transport recovery and explicit close must not erase structural lineage."""

from types import SimpleNamespace

import pytest

from acp_adapter.session import SessionManager
from hermes_state import SessionDB


@pytest.mark.parametrize("reason", ["acp_disconnect", "acp_close", "compression", "reset"])
@pytest.mark.parametrize("explicit", [False, True])
def test_restore_respects_end_reason_and_preserves_history(tmp_path, reason, explicit):
    with SessionDB(tmp_path / "state.db") as db:
        db.create_session("session", source="acp")
        db.append_message("session", "user", "canonical history")
        db.end_session("session", reason)
        before = db.get_messages("session", include_inactive=True)
        manager = SessionManager(
            agent_factory=lambda: SimpleNamespace(model="test", _session_db=db, _session_db_created=True), db=db
        )
        state = (manager.update_cwd("session", str(tmp_path), reopen=True)
                 if explicit else manager.get_session("session"))
        allowed = explicit or reason == "acp_disconnect"
        assert (state is not None) == allowed
        row = db.get_session("session")
        reopened = reason == "acp_disconnect" or (explicit and reason == "acp_close")
        assert (row["ended_at"] is None) == reopened
        assert row["end_reason"] == (None if reopened else reason)
        assert db.get_messages("session", include_inactive=True) == before


@pytest.mark.parametrize("reason", ["acp_disconnect", "acp_close"])
@pytest.mark.parametrize("failure", ["history", "factory"])
def test_failed_restore_keeps_original_end_boundary(tmp_path, monkeypatch, reason, failure):
    with SessionDB(tmp_path / "state.db") as db:
        db.create_session("session", source="acp")
        db.append_message("session", "user", "keep me")
        db.end_session("session", reason)
        before = db.get_messages("session", include_inactive=True)

        def fail(*args, **kwargs):
            raise RuntimeError("restore unavailable")

        manager = SessionManager(agent_factory=fail, db=db)
        if failure == "history":
            monkeypatch.setattr(db, "get_messages_as_conversation", fail)
        restored = (manager.get_session("session") if reason == "acp_disconnect"
                    else manager.update_cwd("session", str(tmp_path), reopen=True))
        assert restored is None
        row = db.get_session("session")
        assert row["ended_at"] is not None and row["end_reason"] == reason
        assert db.get_messages("session", include_inactive=True) == before
        assert "session" not in manager._sessions
