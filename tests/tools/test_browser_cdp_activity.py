"""Cross-process activity leases for an externally managed CDP browser."""

import json
import threading
import time
from pathlib import Path

import pytest


@pytest.fixture
def configured_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    activity = tmp_path / "cdp-activity"
    home.mkdir()
    (home / "config.yaml").write_text(
        json.dumps({
            "browser": {
                "cdp_url": "http://localhost:9222",
                "cdp_activity_dir": str(activity),
            }
        }),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(home))
    return activity


def test_activity_lease_exists_only_while_browser_call_is_active(configured_home):
    from tools.browser_cdp_activity import activity_lease

    last_used = configured_home / "last_used"
    with activity_lease():
        leases = list((configured_home / "leases").glob("*.lease"))
        assert len(leases) == 1
        assert last_used.is_file()
        entered_mtime = last_used.stat().st_mtime_ns

    assert list((configured_home / "leases").glob("*.lease")) == []
    assert last_used.stat().st_mtime_ns >= entered_mtime


def test_activity_lease_is_disabled_without_a_configured_cdp_endpoint(tmp_path, monkeypatch):
    from tools.browser_cdp_activity import activity_lease

    home = tmp_path / "hermes"
    activity = tmp_path / "cdp-activity"
    home.mkdir()
    (home / "config.yaml").write_text(
        json.dumps({"browser": {"cdp_activity_dir": str(activity)}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(home))

    with activity_lease():
        pass

    assert not activity.exists()


def test_active_lease_heartbeat_refreshes_its_mtime(configured_home, monkeypatch):
    from tools import browser_cdp_activity as activity

    monkeypatch.setattr(activity, "_HEARTBEAT_SECONDS", 0.01)
    with activity.activity_lease():
        lease = next((configured_home / "leases").glob("*.lease"))
        initial = lease.stat().st_mtime_ns
        deadline = time.monotonic() + 1
        while lease.stat().st_mtime_ns == initial and time.monotonic() < deadline:
            time.sleep(0.01)
        assert lease.stat().st_mtime_ns > initial


def test_heartbeat_start_failure_does_not_leak_a_lease(configured_home, monkeypatch):
    from agent import memory_provider
    from tools.browser_cdp_activity import activity_lease

    def fail_to_build_thread(*args, **kwargs):
        raise RuntimeError("thread unavailable")

    monkeypatch.setattr(memory_provider, "spawn_context_thread", fail_to_build_thread)

    with pytest.raises(RuntimeError, match="thread unavailable"):
        with activity_lease():
            pass

    assert list((configured_home / "leases").glob("*.lease")) == []


def test_exception_inside_operation_releases_lease(configured_home):
    from tools.browser_cdp_activity import activity_lease

    with pytest.raises(RuntimeError, match="operation failed"):
        with activity_lease():
            raise RuntimeError("operation failed")

    assert list((configured_home / "leases").glob("*.lease")) == []


def test_concurrent_operations_publish_independent_leases(configured_home):
    from tools.browser_cdp_activity import activity_lease

    both_entered = threading.Barrier(3)
    release = threading.Event()

    def hold_lease():
        with activity_lease():
            both_entered.wait(timeout=2)
            release.wait(timeout=2)

    threads = [threading.Thread(target=hold_lease) for _ in range(2)]
    for thread in threads:
        thread.start()
    both_entered.wait(timeout=2)
    assert len(list((configured_home / "leases").glob("*.lease"))) == 2
    release.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert list((configured_home / "leases").glob("*.lease")) == []
