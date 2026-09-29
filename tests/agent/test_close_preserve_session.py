"""A retired ACP runtime releases clients, not its replacement's session."""

import threading
from unittest.mock import MagicMock

from hermes_state import SessionDB
from run_agent import AIAgent


def test_retirement_keeps_shared_session_and_task_resources_live(tmp_path):
    with SessionDB(tmp_path / "state.db") as db:
        db.create_session("shared", source="acp")
        db.append_message("shared", "user", "retained")
        old = AIAgent.__new__(AIAgent)
        old.session_id = "shared"
        old._session_db = db
        old._owns_session_db = False
        old._end_session_on_close = True
        old._active_children_lock = threading.Lock()
        old._active_children = set()
        old._session_messages = [{"role": "user", "content": "retained"}]
        old.client = MagicMock()
        client = old.client
        old._codex_session = MagicMock()
        codex = old._codex_session
        old.shutdown_memory_provider = MagicMock()
        old._close_task_resources = MagicMock()
        old._close_openai_client = MagicMock()
        old._close_request_clients = MagicMock()
        old._trim_process_memory = MagicMock()

        old.close(preserve_session=True)

        old._close_task_resources.assert_not_called()
        old.shutdown_memory_provider.assert_called_once()
        old._close_openai_client.assert_called_once_with(client, reason="agent_close", shared=True)
        codex.close.assert_called_once()
        assert old.client is None and old._codex_session is None
        assert old._session_messages == []
        assert db.get_session("shared")["ended_at"] is None
        db.append_message("shared", "assistant", "replacement is still writable")
        assert len(db.get_messages("shared")) == 2
