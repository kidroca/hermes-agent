"""Review regressions using real config readers with external I/O intercepted."""
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
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


@pytest.mark.parametrize("command", [True, False, 123, {"executable": "helper"}, ["helper", 1]])
def test_invalid_yaml_command_continues_discovery(configured, monkeypatch, command):
    configured(cdp_url="http://cdp.invalid:9222", cdp_auto_launch=True,
               cdp_launch_command=command)
    probes = []

    def offline(*args, **kwargs):
        probes.append(kwargs["timeout"])
        raise requests.ConnectionError("offline")

    def forbidden(*args, **kwargs):
        pytest.fail("invalid command must not spawn")

    monkeypatch.setattr(requests, "get", offline)
    monkeypatch.setattr(subprocess, "run", forbidden)
    assert cdp.get_cdp_override() == "http://cdp.invalid:9222"
    assert cdp.get_cdp_override(fallback_to_raw=False) == ""
    assert probes[-1] == 10


@pytest.mark.parametrize("canonical", ["", "   ", "http://canonical.invalid:9222"])
def test_alias_routing_is_pure(configured, monkeypatch, canonical):
    from tools.browser_session_cloud import browser_backend_name, is_local_backend

    configured(cdp_url=canonical, cdp_endpoint="http://alias.invalid:9222", cdp_auto_launch=True,
               cdp_launch_command=["helper"])

    def forbidden(*args, **kwargs):
        pytest.fail("a config gate must not probe or launch")

    monkeypatch.setattr(requests, "get", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    expected = canonical.strip() or "http://alias.invalid:9222"
    assert cdp.get_cdp_override_raw() == expected
    assert is_local_backend() is False
    assert browser_backend_name() == "cdp"
    monkeypatch.setenv("BROWSER_CDP_URL", "http://env.invalid:9222")
    assert cdp.get_cdp_override_raw() == "http://env.invalid:9222"


def test_concurrent_cold_resolution_launches_once(configured, monkeypatch):
    configured(cdp_endpoint="http://cdp.invalid:9222", cdp_auto_launch=True,
               cdp_launch_command=["helper"])
    first_launch = threading.Event()
    duplicate_launch = threading.Event()
    ready = threading.Event()
    launches = []

    def get(*args, **kwargs):
        if not ready.is_set():
            raise requests.ConnectionError("offline")
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"webSocketDebuggerUrl": "ws://cdp.invalid/devtools/browser/new"})

    def run(argv, **kwargs):
        launches.append(argv)
        if len(launches) == 1:
            first_launch.set()
            duplicate_launch.wait(2)
        else:
            duplicate_launch.set()
        ready.set()
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(subprocess, "run", run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(cdp.get_cdp_override)
        assert first_launch.wait(5)
        second = pool.submit(cdp.get_cdp_override)
        assert first.result(timeout=8) == second.result(timeout=8)
    assert launches == [["helper"]]


def test_launch_locks_are_scoped_to_the_configured_endpoint():
    first = cdp._launch_lock_for("http://first.invalid:9222")
    assert first is cdp._launch_lock_for("http://first.invalid:9222")
    assert first is not cdp._launch_lock_for("http://second.invalid:9222")


@pytest.mark.parametrize("contended", [False, True])
def test_failed_helper_retry_and_bounded_contention(configured, monkeypatch, contended):
    configured(cdp_url="http://cdp.invalid:9222", cdp_auto_launch=True,
               cdp_launch_command=["helper"])
    launches, waits = [], []

    def offline(*args, **kwargs):
        raise requests.ConnectionError("offline")

    def run(argv, **kwargs):
        launches.append(argv)
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    def acquire(*, timeout):
        waits.append(timeout)
        return False

    monkeypatch.setattr(requests, "get", offline)
    monkeypatch.setattr(subprocess, "run", run)
    if contended:
        monkeypatch.setattr(cdp, "_launch_lock_for", lambda _endpoint: SimpleNamespace(acquire=acquire))
    # Retrying an idempotent helper after failure is supported, not cached forever.
    assert cdp.get_cdp_override() == "http://cdp.invalid:9222"
    assert cdp.get_cdp_override(fallback_to_raw=False) == ""
    assert launches == ([] if contended else [["helper"], ["helper"]])
    assert waits == ([16, 16] if contended else [])
