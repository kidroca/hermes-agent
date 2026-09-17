"""Retained CDP contract: real config readers and owners, stubbed external I/O."""
import json
import subprocess
from types import SimpleNamespace

import pytest
import requests

from tools import browser_session_cdp as cdp


@pytest.fixture
def configured(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    def write(**values):
        (tmp_path / "config.yaml").write_text(json.dumps({"browser": values}))
    return write


def test_discovery_alias_is_pure_and_first_use_launches_argv(configured, monkeypatch):
    from tools import browser_session, browser_session_lifecycle
    configured(cdp_endpoint="http://cdp.invalid:9222", cdp_auto_launch=True,
               cdp_launch_command='helper "two words" ; literal')
    events = []
    def get(url, **kw):
        events.append(("probe", kw["timeout"]))
        if len(events) == 1:
            raise requests.ConnectionError("not running")
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"webSocketDebuggerUrl": "ws://cdp.invalid/devtools/browser/new"})
    def run(argv, **kw):
        events.append(("launch", argv))
        assert kw.get("shell", False) is False
        assert 0 < kw["timeout"] <= 15
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(subprocess, "run", run)
    assert cdp.get_cdp_override_raw() == "http://cdp.invalid:9222"
    assert events == []
    monkeypatch.setattr(browser_session, "_active_sessions", {})
    monkeypatch.setattr(browser_session, "_session_last_activity", {})
    monkeypatch.setattr(browser_session_lifecycle, "start_cleanup_thread", lambda: None)
    monkeypatch.setattr(browser_session_lifecycle, "update_session_activity", lambda _: None)
    monkeypatch.setattr("tools.browser_supervisor.SUPERVISOR_REGISTRY.get_or_start", lambda **kw: None)
    session = browser_session.get_session_info("lazy-cdp-test")
    assert session["cdp_url"] == "ws://cdp.invalid/devtools/browser/new"
    assert events[:3] == [("probe", 1), ("launch", ["helper", "two words", ";", "literal"]), ("probe", 10)]
    # Supervisor attachment rediscovers instead of caching a process-specific UUID.
    assert all(event == ("probe", 1) for event in events[3:])


@pytest.mark.parametrize("config_enabled", [False, True])
def test_launch_gate_is_config_only_and_no_stale_websocket(configured, monkeypatch, config_enabled):
    """Launch knobs come from the profile's config only: process env holds the launch profile's values."""
    configured(cdp_url="http://config.invalid:9222", cdp_auto_launch=config_enabled,
               cdp_launch_command=["config-helper"])
    monkeypatch.setenv("BROWSER_CDP_URL", "http://env.invalid:9222")
    monkeypatch.setenv("BROWSER_CDP_AUTO_LAUNCH", "true")
    monkeypatch.setenv("BROWSER_CDP_LAUNCH_COMMAND", "env-helper")
    probes, launches = [], []
    def get(url, **kw):
        probes.append((url, kw["timeout"]))
        if len(probes) == 1:
            raise requests.ConnectionError("offline")
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"webSocketDebuggerUrl": f"ws://env.invalid/devtools/browser/{len(probes)}"})
    def run(argv, **kw):
        launches.append(argv)
        raise subprocess.TimeoutExpired(argv, kw["timeout"])
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(subprocess, "run", run)
    first = cdp.get_cdp_override()
    second = cdp.get_cdp_override()
    assert probes[0][0] == "http://env.invalid:9222/json/version"
    assert second.endswith(f"/{len(probes)}")
    if config_enabled:
        assert launches == [["config-helper"]]
        assert first.endswith("/2")
        assert probes[0][1] == 1
    else:
        assert launches == []
        assert first == "http://env.invalid:9222"


def test_resolution_policy_is_per_call(configured, monkeypatch):
    configured(cdp_url="http://cdp.invalid:9222")
    def fail(*args, **kwargs):
        assert kwargs["timeout"] == 2
        raise requests.ConnectionError("offline")
    monkeypatch.setattr(requests, "get", fail)
    assert cdp.get_cdp_override(timeout=2, fallback_to_raw=False) == ""
    assert cdp.get_cdp_override(timeout=2) == "http://cdp.invalid:9222"


@pytest.mark.parametrize("command,expected", [(["helper", "space arg"], ["helper", "space arg"]),
                                            ('"unterminated', None), ([], None)])
def test_launch_command_validation(command, expected, monkeypatch):
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == 15
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, "run", run)
    assert cdp._run_cdp_launch_command(command) is (expected is not None)
    assert calls == ([] if expected is None else [expected])
