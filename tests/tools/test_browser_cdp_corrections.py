"""Review regressions using real config readers with external I/O intercepted."""
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import requests

from tools import browser_tool_cdp as cdp


@pytest.fixture
def configured(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    for name in ("BROWSER_CDP_URL", "BROWSER_CDP_AUTO_LAUNCH", "BROWSER_CDP_LAUNCH_COMMAND"):
        monkeypatch.delenv(name, raising=False)

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
    assert cdp._get_cdp_override() == "http://cdp.invalid:9222"
    assert cdp._get_cdp_override(fallback_to_raw=False) == ""
    assert probes[-1] == 10


@pytest.mark.parametrize("canonical", ["", "   ", "http://canonical.invalid:9222"])
def test_camofox_alias_routing_is_pure(configured, monkeypatch, canonical):
    from tools import browser_camofox
    from tools.browser_tool_cloud import _is_local_mode, _is_local_backend
    from tools.browser_cdp_tool import _browser_cdp_check

    configured(cloud_provider="camofox", cdp_url=canonical,
               cdp_endpoint="http://alias.invalid:9222", cdp_auto_launch=True,
               cdp_launch_command=["helper"])

    def forbidden(*args, **kwargs):
        pytest.fail("a config gate must not probe or launch")

    monkeypatch.setattr(requests, "get", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    expected = canonical.strip() or "http://alias.invalid:9222"
    assert browser_camofox._config_cdp_url() == cdp._get_cdp_override_raw() == expected
    assert browser_camofox.is_camofox_mode() is False
    assert _is_local_mode() is False
    assert _is_local_backend() is False
    assert _browser_cdp_check() is True
    monkeypatch.setenv("BROWSER_CDP_URL", "http://env.invalid:9222")
    assert cdp._get_cdp_override_raw() == "http://env.invalid:9222"
    assert browser_camofox.is_camofox_mode() is False


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
        first = pool.submit(cdp._get_cdp_override)
        assert first_launch.wait(5)
        second = pool.submit(cdp._get_cdp_override)
        assert first.result(timeout=8) == second.result(timeout=8)
    assert launches == [["helper"]]


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
        monkeypatch.setattr(cdp, "_cdp_launch_lock", SimpleNamespace(acquire=acquire))
    # Retrying an idempotent helper after failure is supported, not cached forever.
    assert cdp._get_cdp_override() == "http://cdp.invalid:9222"
    assert cdp._get_cdp_override(fallback_to_raw=False) == ""
    assert launches == ([] if contended else [["helper"], ["helper"]])
    assert waits == ([16, 16] if contended else [])
