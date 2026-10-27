"""The in-process ticker preserves shared delivery and disconnected bot boundaries."""

import threading

import pytest


@pytest.mark.parametrize("owns_bot", [False, True])
def test_local_session_does_not_hide_shared_route_from_tick(tmp_path, monkeypatch, owns_bot):
    from cron import scheduler
    from cron.scheduler_ownership import register_ticked_homes
    from cron.scheduler_preflight import SharedRouteAdapters
    from cron.scheduler_provider import InProcessCronScheduler
    from gateway.config import Platform
    from gateway.profile_routing import ProfileRoute

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    own = {Platform.LOCAL: object()}
    primary = object()
    stop = threading.Event()
    observed = []
    monkeypatch.setattr("cron.scheduler_preflight._primary_profile_routes_for_current_home", lambda: [
        ProfileRoute("satellite", "discord", "satellite", chat_id="C1", guild_id="G1")])
    provider = InProcessCronScheduler()
    monkeypatch.setattr(provider, "recover_interrupted", lambda: 0)

    def tick(**kwargs):
        observed.append(kwargs["adapters"])
        stop.set()

    monkeypatch.setattr(scheduler, "tick", tick)
    try:
        provider.start(
            stop, profile_homes=[("satellite", tmp_path)], default_profile="default",
            adapters={Platform.DISCORD: primary}, profile_adapters={"satellite": own},
            profile_bot_platforms={"satellite": {Platform.DISCORD}} if owns_bot else {},
        )
    finally:
        register_ticked_homes([])
    assert len(observed) == 1
    if owns_bot:
        assert observed[0] is own
        assert observed[0].get(Platform.DISCORD) is None
    else:
        assert isinstance(observed[0], SharedRouteAdapters)
        assert observed[0].get(Platform.DISCORD, {"chat_id": "C1"}) is primary
        assert observed[0].get(Platform.DISCORD, {"chat_id": "C9"}) is None
