"""Cross-process activity leases for an externally managed CDP browser."""

import json
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
