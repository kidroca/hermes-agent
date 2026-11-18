"""Repeated sync failures back off instead of re-running the transfer before every command.

A single failure still retries on the very next cycle (#39945/#40048): only a second
consecutive failure starts a capped exponential backoff, and any success resets it.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.environments import file_sync
from tools.environments.file_sync import FileSyncManager


@pytest.fixture
def clock(monkeypatch):
    now = {"t": 1000.0}
    monkeypatch.setattr(file_sync, "_monotonic", lambda: now["t"])
    return now


def _manager(tmp_path, upload):
    source = tmp_path / "skill.md"
    source.write_text("skill", encoding="utf-8")
    return FileSyncManager(lambda: [(str(source), "/remote/.hermes/skill.md")], upload, lambda paths: None,
                           sync_interval=5.0)


def _fail_twice(mgr, upload, clock):
    upload.side_effect = RuntimeError("SSH bulk upload timed out")
    mgr.sync(force=True)
    clock["t"] += 1
    mgr.sync()  # first failure retries immediately — the existing contract
    assert upload.call_count == 2


def test_second_consecutive_failure_backs_off(tmp_path, clock):
    upload = MagicMock()
    mgr = _manager(tmp_path, upload)
    _fail_twice(mgr, upload, clock)

    clock["t"] += 29
    mgr.sync()
    assert upload.call_count == 2, "inside the 30 s backoff the transport must not be touched"

    clock["t"] += 2
    mgr.sync()
    assert upload.call_count == 3, "after the backoff the remainder is retried"


def test_backoff_grows_and_is_capped(tmp_path, clock):
    upload = MagicMock()
    mgr = _manager(tmp_path, upload)
    _fail_twice(mgr, upload, clock)
    delays = []
    for _ in range(6):
        start, calls = clock["t"], upload.call_count
        while upload.call_count == calls:
            clock["t"] += 1
            mgr.sync()
        delays.append(round(clock["t"] - start))
    assert delays == [30, 60, 120, 240, 300, 300]


def test_success_resets_the_failure_streak(tmp_path, clock):
    upload = MagicMock()
    mgr = _manager(tmp_path, upload)
    _fail_twice(mgr, upload, clock)

    clock["t"] += 31
    upload.side_effect = None
    mgr.sync()
    assert upload.call_count == 3
    assert mgr._last_sync_time == clock["t"]

    Path(tmp_path / "skill.md").write_text("changed skill", encoding="utf-8")
    upload.side_effect = RuntimeError("blip")
    clock["t"] += 6
    mgr.sync()
    clock["t"] += 1
    upload.side_effect = None
    mgr.sync()
    assert upload.call_count == 5, "a fresh single failure retries immediately again"


def test_force_bypasses_backoff(tmp_path, clock):
    upload = MagicMock()
    mgr = _manager(tmp_path, upload)
    _fail_twice(mgr, upload, clock)

    clock["t"] += 1
    mgr.sync(force=True)
    assert upload.call_count == 3
