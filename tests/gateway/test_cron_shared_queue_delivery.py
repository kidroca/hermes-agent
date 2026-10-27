"""Queued satellite delivery retains the target-exact shared bot grant (#143953 B)."""

import asyncio
import threading
from types import SimpleNamespace

import pytest
import hermes_yaml as yaml

from cron import delivery_queue
from gateway.config import Platform
import gateway.run as gateway_run
from hermes_constants import reset_hermes_home_override, set_hermes_home_override


@pytest.mark.parametrize(
    "case, target, route_changes, own_bot, expected",
    [
        ("authorized", "C1", {}, False, "delivered"),
        ("unmatched", "C9", {}, False, "failed"),
        ("disabled", "C1", {"enabled": False}, False, "failed"),
        ("other-profile", "C1", {"profile": "other"}, False, "failed"),
        ("guild-only", "C1", {"chat_id": None}, False, "failed"),
        ("owned-bot-down", "C1", {}, True, "failed"),
        ("primary", "C1", {}, False, "delivered"),
    ],
)
def test_queue_drain_authorizes_shared_transport_once(
    tmp_path, monkeypatch, case, target, route_changes, own_bot, expected,
):
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / ".hermes"
    satellite = root / "profiles" / "satellite"
    satellite.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setattr("hermes_constants.get_default_hermes_root", lambda: root)
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    route = {"platform": "discord", "guild_id": "G1", "chat_id": "C1", "profile": "satellite"}
    route.update(route_changes)
    (root / "config.yaml").write_text(yaml.safe_dump({
        "gateway": {"multiplex_profiles": True, "profile_routes": [route]},
        "platforms": {"discord": {"enabled": True, "token": "synthetic-token"}},
        "cron": {"wrap_response": False},
    }), encoding="utf-8")
    (satellite / "config.yaml").write_text(yaml.safe_dump({
        "platforms": {"discord": {"enabled": False}},
        "cron": {"wrap_response": False},
    }), encoding="utf-8")
    sent = []

    class PrimaryAdapter:
        async def send(self, chat_id, content, metadata=None):
            sent.append((chat_id, content))
            return {"success": True, "message_id": "synthetic-message"}

    async def refuse_standalone(*args, **kwargs):
        pytest.fail("queue delivery must never invoke a standalone sender")

    monkeypatch.setattr("tools.send_message_tool._send_to_platform", refuse_standalone)
    home = root if case == "primary" else satellite
    profile = None if case == "primary" else "satellite"
    runner = SimpleNamespace(
        _profile_adapters={"satellite": {Platform.LOCAL: object()}},
        _profile_bot_platforms={"satellite": {Platform.DISCORD}} if own_bot else {},
    )
    monkeypatch.setattr(gateway_run, "_handoff_watch_scopes", lambda r: [(profile, home)])
    token = set_hermes_home_override(str(home))
    try:
        delivery_queue.enqueue("execution", {"id": "job", "deliver": f"discord:{target}"}, "queued output")
    finally:
        reset_hermes_home_override(token)

    loop = asyncio.new_event_loop()
    ready = threading.Event()
    loop.call_soon(ready.set)
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    try:
        assert ready.wait(5), "adapter loop did not start"
        adapters = {Platform.DISCORD: PrimaryAdapter()}
        gateway_run._drain_restart_safe_cron_deliveries(adapters, loop, runner)
        gateway_run._drain_restart_safe_cron_deliveries(adapters, loop, runner)
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)
        assert not thread.is_alive(), "adapter loop did not stop"
        loop.close()
    token = set_hermes_home_override(str(home))
    try:
        row = delivery_queue.get_status("execution")
    finally:
        reset_hermes_home_override(token)
    assert row["status"] == expected, row
    assert sent == ([(target, "queued output")] if expected == "delivered" else [])
