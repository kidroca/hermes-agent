"""Exact-entry public identity is captured in the caller, never from a mirror."""
from hermes_constants import set_hermes_home_override, reset_hermes_home_override
from gateway import session_context as sessions
from tools import approval_context as context
from tools.approval_gateway_wait import _ApprovalEntry


def test_entry_captures_bound_identity_and_copies_metadata(tmp_path):
    home = set_hermes_home_override(tmp_path / "profiles" / "alpha")
    tokens = context.set_current_observability_context(session_id="durable-A")
    sessions.set_session_vars(session_id="durable-A", profile="alpha")
    try:
        first = _ApprovalEntry({"command": "same", "display_context": {"profile": "spoof"}})
        assert first.data["display_context"] == {"session_id": "durable-A", "profile": "alpha"}
        sessions.set_session_vars(session_id="durable-B", profile="alpha")
        assert "display_context" not in _ApprovalEntry({"command": "same"}).data
        assert first.data["display_context"]["session_id"] == "durable-A"
    finally:
        sessions.clear_session_vars([])
        context.reset_current_observability_context(tokens)
        reset_hermes_home_override(home)


def test_unbound_environment_and_caller_metadata_cannot_supply_identity(monkeypatch):
    sessions.reset_session_vars()
    monkeypatch.setenv("HERMES_SESSION_ID", "private-environment")
    monkeypatch.setenv("HERMES_SESSION_PROFILE", "wrong")
    entry = _ApprovalEntry({"display_context": {"session_id": "spoof"}})
    assert "display_context" not in entry.data


def test_title_uses_only_exact_owner_getter_and_snapshot_is_detached(tmp_path):
    from types import SimpleNamespace
    from tools.approval_display import approval_display_scope
    from tools import approval
    from unittest.mock import Mock
    home = set_hermes_home_override(tmp_path / "profiles" / "alpha")
    tokens = context.set_current_observability_context(session_id="durable-A")
    sessions.set_session_vars(session_id="durable-A", profile="alpha")
    getter = Mock(return_value="Public title")
    try:
        with approval_display_scope(SimpleNamespace(session_id="durable-A", _session_db=SimpleNamespace(get_session_title=getter))):
            entry = _ApprovalEntry({"command": "same"})
        getter.assert_called_once_with("durable-A")
        approval._gateway_queues["synthetic-display"] = [entry]
        row = approval.list_gateway_approvals("synthetic-display")[0]
        row["display_context"]["session_title"] = "tampered"
        assert entry.data["display_context"]["session_title"] == "Public title"
        with approval_display_scope(SimpleNamespace(session_id="other", _session_db=SimpleNamespace(get_session_title=getter))):
            assert "session_title" not in _ApprovalEntry({}).data["display_context"]
        getter.assert_called_once()
    finally:
        approval._gateway_queues.pop("synthetic-display", None)
        sessions.clear_session_vars([])
        context.reset_current_observability_context(tokens)
        reset_hermes_home_override(home)


def test_public_fields_fail_closed_and_are_bounded(monkeypatch):
    from tools.approval_display import _public
    from agent.think_scrubber import THINK_TAG_NAMES
    for tag in (*THINK_TAG_NAMES, "analysis"):
        assert _public(f"public </{tag} secret", 240) is None
        assert _public(f"<{tag} attr=x>private", 240) is None
    assert _public("[System: private]", 240) is None
    assert len(_public("я" * 8000, 240)) == 240
    assert _public("a" * 241, 240, identity=True) is None
    assert _public("durable\nDisplay session: other", 240, identity=True) is None
    assert _public("title\u202eprivate", 240) is None
    assert "synthetic-secret-value" not in _public("api_key=synthetic-secret-value", 240)
    monkeypatch.setattr("agent.redact.redact_sensitive_text", lambda *a, **k: (_ for _ in ()).throw(ValueError("synthetic")))
    assert _public("public", 240) is None


def test_concurrent_profiles_and_reset_do_not_reuse_identity(tmp_path):
    import concurrent.futures
    import contextvars
    def build(profile):
        home = set_hermes_home_override(tmp_path / "profiles" / profile)
        obs = context.set_current_observability_context(session_id="same-durable")
        sessions.set_session_vars(session_id="same-durable", profile=profile)
        try:
            parent = contextvars.copy_context()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                entry = pool.submit(parent.run, _ApprovalEntry, {"command": "same"}).result()
            sessions.reset_session_vars()
            assert "display_context" not in _ApprovalEntry({}).data
            return entry.data["display_context"]
        finally:
            context.reset_current_observability_context(obs)
            reset_hermes_home_override(home)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(pool.map(build, ("alpha", "beta")))
    assert a == {"session_id": "same-durable", "profile": "alpha"}
    assert b == {"session_id": "same-durable", "profile": "beta"}


def test_waiter_uses_owner_routing_and_does_not_invent_missing_profile(monkeypatch):
    from tools import approval_gateway_wait as wait
    tokens = context.set_current_observability_context(session_id="durable")
    routing = context.set_current_session_key("route")
    sessions.set_session_vars(session_id="durable", session_key="route")
    monkeypatch.setattr(wait, "_poll_event", lambda *a, **k: "timeout")
    seen = []
    try:
        wait._await_gateway_decision("route", seen.append, {"command": "inert"})
        assert seen[0]["display_context"] == {"session_id": "durable"}
        wait._await_gateway_decision("other-route", seen.append, {"command": "inert"})
        assert "display_context" not in seen[1]
    finally:
        sessions.clear_session_vars([])
        context.reset_current_session_key(routing)
        context.reset_current_observability_context(tokens)


def test_real_tool_worker_uses_title_getter_only_and_restores_scope(tmp_path):
    import threading
    from types import SimpleNamespace
    from agent.tool_executor import _registered_tool_worker
    calls = []
    class PublicDB:
        def get_session_title(self, sid):
            calls.append(sid)
            return "exact public title"
    agent = SimpleNamespace(session_id="durable", _session_db=PublicDB(),
        _tool_worker_threads_lock=threading.Lock(), _tool_worker_threads=set())
    home = set_hermes_home_override(tmp_path / "profiles" / "alpha")
    obs = context.set_current_observability_context(session_id="durable")
    sessions.set_session_vars(session_id="durable", profile="alpha")
    try:
        with _registered_tool_worker(agent):
            assert _ApprovalEntry({}).data["display_context"]["session_title"] == "exact public title"
        assert "session_title" not in _ApprovalEntry({}).data["display_context"]
        assert not agent._tool_worker_threads
        assert calls == ["durable"]
    finally:
        sessions.clear_session_vars([])
        context.reset_current_observability_context(obs)
        reset_hermes_home_override(home)
