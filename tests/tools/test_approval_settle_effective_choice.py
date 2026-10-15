"""Settlement observers must agree with the effective verdict, without implying execution."""
import pytest
from tools import approval, approval_gateway_wait as wait


@pytest.mark.parametrize("state,expected", [("timeout", "resolved"), ("interrupted", "interrupted")])
def test_committed_choice_racing_poll_settles_truthfully(monkeypatch, state, expected):
    reasons = []
    key = "synthetic-peer-race"
    def notify(data):
        assert approval.register_gateway_settle(key, data["request_id"], reasons.append)
    def poll(*args, **kwargs):
        row = approval.list_gateway_approvals(key)[0]
        assert approval.resolve_gateway_approval(key, "once", request_id=row["request_id"]) == 1
        return state
    monkeypatch.setattr(wait, "_poll_event", poll)
    result = wait._await_gateway_decision(key, notify, {"command": "inert"})
    assert result["choice"] == ("deny" if state == "interrupted" else "once")
    assert reasons == [expected]
    assert not approval.list_gateway_approvals(key)


def test_observer_failure_cannot_change_host_verdict(monkeypatch):
    key = "synthetic-failing-observer"
    def notify(data):
        def broken(reason):
            raise RuntimeError("synthetic observer error")
        assert approval.register_gateway_settle(key, data["request_id"], broken)
        assert approval.resolve_gateway_approval(key, "deny", request_id=data["request_id"]) == 1
    monkeypatch.setattr(wait, "_poll_event", lambda *a, **k: "set")
    result = wait._await_gateway_decision(key, notify, {"command": "inert"})
    assert result == {"resolved": True, "choice": "deny", "reason": None}
    assert not approval.list_gateway_approvals(key)
