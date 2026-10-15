"""Optional public identity captured by the authoritative approval entry.

This is display data, never a routing key or an execution grant. No environment
fallbacks, conversation bodies or database construction are permitted here.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_title_owner = ContextVar("approval_title_owner", default=None)


@contextmanager
def approval_display_scope(agent):
    """Bind only the owning agent’s exact-ID public title getter for this worker."""
    db = getattr(agent, "_session_db", None)
    owner = (getattr(agent, "session_id", None), getattr(db, "get_session_title", None))
    token = _title_owner.set(owner)
    try:
        yield
    finally:
        _title_owner.reset(token)


def _public(value, limit, *, identity=False):
    from unicodedata import category
    from agent.redact import REDACTION_UNAVAILABLE, redact_for_egress
    from agent.think_scrubber import THINK_TAG_NAMES
    if not isinstance(value, str) or not value.strip() or len(value) > 8192:
        return None
    if any(category(char).startswith("C") for char in value):
        return None
    lower = value.lower()
    if any(prefix + name.lower() in lower for name in (*THINK_TAG_NAMES, "analysis") for prefix in ("<", "</")):
        return None
    if value.lstrip().startswith("[System:"):
        return None
    safe = redact_for_egress(value)
    if safe == REDACTION_UNAVAILABLE or (identity and (safe != value or len(value) > limit)):
        return None
    return safe[:limit]


def capture_display_context(session_key=None):
    """Fail closed unless task-local observability and durable session bindings agree."""
    from gateway.session_context import get_bound_session_env
    from tools.approval_context import _approval_session_id, _approval_session_key
    from hermes_constants import get_hermes_home_override, profile_name_for_home
    try:
        if session_key is not None:
            routing = _approval_session_key.get()
            bound_routing = get_bound_session_env("HERMES_SESSION_KEY")
            if session_key != (routing or bound_routing) or (routing and bound_routing and routing != bound_routing):
                return {}
        sid = get_bound_session_env("HERMES_SESSION_ID")
        if not sid or sid != _approval_session_id.get():
            return {}
        public_sid = _public(sid, 240, identity=True)
        if not public_sid:
            return {}
        result = {"session_id": public_sid}
        profile = get_bound_session_env("HERMES_SESSION_PROFILE")
        home = get_hermes_home_override()
        # A label without the owning runtime home cannot prove profile-local lookup.
        if home and profile and profile == profile_name_for_home(home):
            if safe_profile := _public(profile, 128, identity=True):
                result["profile"] = safe_profile
            owner = _title_owner.get()
            if owner and owner[0] == sid and callable(owner[1]):
                if title := _public(owner[1](sid), 240):
                    result["session_title"] = title
        return result
    except Exception:  # health: allow BLE001 -- optional display lookup/redaction must fail closed without logging public or private metadata
        return {}
