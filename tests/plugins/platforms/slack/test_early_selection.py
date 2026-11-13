"""Early Slack selection through a real, out-of-tree plugin registration."""
from unittest.mock import AsyncMock

import pytest

from gateway.config import PlatformConfig
from hermes_cli import plugins
from hermes_constants import set_hermes_home_override, reset_hermes_home_override
from plugins.platforms.slack.adapter import SlackAdapter


@pytest.fixture
def plugin_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    plugins._reset_plugin_managers_for_tests()
    yield tmp_path
    plugins._reset_plugin_managers_for_tests()


def install_selector(home, body="return 'select'", *, async_callback=False):
    directory = home / "plugins" / "selection-test"
    directory.mkdir(parents=True)
    (directory / "plugin.yaml").write_text(
        "name: selection-test\nversion: 0.1.0\ndescription: Selection contract fixture\n")
    (directory / "__init__.py").write_text(
        ("async " if async_callback else "") + "def select(event_json, **kwargs):\n    " + body + "\n"
        "def register(ctx):\n    ctx.register_hook('pre_platform_message', select)\n")
    (home / "config.yaml").write_text("plugins:\n  enabled: [selection-test]\n")


def make_adapter():
    adapter = SlackAdapter(PlatformConfig(enabled=True, extra={
        "allow_bots": "none", "require_mention": True, "strict_mention": True,
    }))
    adapter._bot_user_id = "U_SELF"
    adapter._team_bot_user_ids = {"T_TEST": "U_SELF"}
    adapter._resolve_user_is_bot = AsyncMock(return_value=True)
    adapter._resolve_user_name = AsyncMock(return_value="CI bot")
    adapter._hydrate_thread_context = AsyncMock(return_value=("", [], []))
    adapter._collect_inbound_media = AsyncMock(return_value=([], [], False, "Build failed"))
    adapter.handle_message = AsyncMock()
    return adapter


def event(**extra):
    return {"type": "message", "subtype": "bot_message", "bot_id": "B_CI",
            "user": "U_CI", "channel": "C_TEST", "channel_type": "channel",
            "team": "T_TEST", "ts": "1700000000.001", "text": "Build failed", **extra}


@pytest.mark.asyncio
async def test_selected_root_reaches_native_message_routing(plugin_home):
    install_selector(plugin_home)
    adapter = make_adapter()
    adapter.set_authorization_check(lambda *args, **kwargs: True)
    incoming = event()
    await adapter._handle_slack_message(incoming)
    adapter.handle_message.assert_awaited_once()
    message = adapter.handle_message.call_args.args[0]
    assert message.source.thread_id == incoming["ts"]
    assert message.source.user_id == "U_CI"
    assert message.source.is_bot is True
    assert message.source.chat_id == "C_TEST"
    assert message.source.scope_id == "T_TEST"
    assert message.source._transport_adapter_ref() is adapter
    assert incoming == event()


@pytest.mark.asyncio
async def test_environment_home_change_cannot_rebind_selector(plugin_home, monkeypatch):
    install_selector(plugin_home)
    adapter = make_adapter()
    other = plugin_home / 'other'
    install_selector(other, "return 'skip'")
    monkeypatch.setenv('HERMES_HOME', str(other))
    await adapter._handle_slack_message(event())
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize('body', ["return 'skip'", "return None", "return True", "raise ValueError('broken')"])
async def test_invalid_or_skip_drops_otherwise_native_eligible_event(plugin_home, body):
    install_selector(plugin_home, body)
    adapter = make_adapter()
    adapter._resolve_user_is_bot = AsyncMock(return_value=False)
    await adapter._handle_slack_message(event(subtype=None, bot_id=None, text='<@U_SELF> hi'))
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("sender", [
    {"user": "U_SELF"},
    {"user": None, "bot_profile": {"user_id": "U_SELF"}},
    {"user": None, "bot_id": "B_SELF"},
    {"user": None, "bot_profile": {"id": "B_SELF"}},
    {"user": None, "team": "", "bot_id": "B_SELF"},
])
async def test_select_cannot_admit_self_echo(plugin_home, sender):
    install_selector(plugin_home)
    adapter = make_adapter()
    adapter._team_bot_ids = {"T_TEST": "B_SELF"}
    await adapter._handle_slack_message(event(**sender))
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_raw_flag_is_not_selection(plugin_home):
    adapter = make_adapter()
    adapter._resolve_user_is_bot = AsyncMock(return_value=False)
    adapter._should_wake_on_unmentioned_message = AsyncMock(return_value=False)
    await adapter._handle_slack_message(event(
        user="U_HUMAN", bot_id=None, subtype=None, _hermes_force_process=True))
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [None, "return 'delegate'", "return 'skip'", "return None",
                                  "return True", "return {'action': 'select'}",
                                  "raise RuntimeError('broken selector')"])
async def test_non_selection_keeps_bot_blocked(plugin_home, body):
    if body is not None:
        install_selector(plugin_home, body)
    adapter = make_adapter()
    await adapter._handle_slack_message(event())
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [None, "return 'delegate'"])
async def test_native_human_mention_still_routes(plugin_home, body):
    if body is not None:
        install_selector(plugin_home, body)
    adapter = make_adapter()
    adapter._resolve_user_is_bot = AsyncMock(return_value=False)
    await adapter._handle_slack_message(event(
        user="U_HUMAN", bot_id=None, subtype=None, text="<@U_SELF> hello"))
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [
    {"allowed_channels": "C_OTHER"}, {"ignored_channels": "C_TEST"},
    {"disable_dms": True},
])
async def test_selection_preserves_channel_policy(plugin_home, extra):
    install_selector(plugin_home)
    adapter = make_adapter()
    adapter.config.extra.update(extra)
    incoming = event(channel="D_TEST", channel_type="im") if "disable_dms" in extra else event()
    await adapter._handle_slack_message(incoming)
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_selection_preserves_early_authorization(plugin_home):
    install_selector(plugin_home)
    adapter = make_adapter()
    adapter.set_authorization_check(lambda *args, **kwargs: False)
    await adapter._handle_slack_message(event())
    adapter.handle_message.assert_not_awaited()
    adapter._collect_inbound_media.assert_not_awaited()


@pytest.mark.asyncio
async def test_selection_preserves_other_user_address_gate(plugin_home):
    install_selector(plugin_home)
    adapter = make_adapter()
    adapter.config.extra["ignore_other_user_mentions"] = True
    await adapter._handle_slack_message(event(text="<@U_OTHER> Build failed"))
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("shape", [
    {"user": None}, {"subtype": None, "bot_id": None, "user_profile": {"is_bot": True}},
    {"subtype": None, "bot_id": None}, {"user": None, "app_id": "A_CI"},
])
async def test_bot_shapes_keep_provenance_and_runner_auth(plugin_home, shape, monkeypatch):
    install_selector(plugin_home)
    adapter = make_adapter()
    await adapter._handle_slack_message(event(**shape))
    adapter.handle_message.assert_awaited_once()
    source = adapter.handle_message.call_args.args[0].source
    assert source.is_bot is True
    assert (source.user_id or "") == (shape.get("user", "U_CI") or "")
    from types import SimpleNamespace
    from gateway.run import GatewayRunner
    runner = object.__new__(GatewayRunner)
    runner.pairing_store = SimpleNamespace(is_approved=lambda *args, **kwargs: False)
    assert runner._is_user_authorized(source) is False
    monkeypatch.setenv("SLACK_ALLOWED_USERS", "U_CI")
    assert runner._is_user_authorized(source) is bool(source.user_id)


@pytest.mark.asyncio
async def test_selection_remains_bound_to_receiving_profile(plugin_home):
    owner, other = plugin_home / "owner", plugin_home / "other"
    install_selector(owner, "from hermes_constants import get_hermes_home; assert str(get_hermes_home()) == kwargs['profile_home']; return 'select'")
    install_selector(other, "return 'skip'")
    token = set_hermes_home_override(str(owner))
    try:
        adapter = make_adapter()
    finally:
        reset_hermes_home_override(token)
    token = set_hermes_home_override(str(other))
    try:
        await adapter._handle_slack_message(event())
    finally:
        reset_hermes_home_override(token)
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_plugin_snapshot_cannot_rewrite_source(plugin_home):
    install_selector(plugin_home,
                     "import json; data = json.loads(event_json); data['user'] = 'U_FORGED'; return 'select'")
    adapter = make_adapter()
    await adapter._handle_slack_message(event())
    assert adapter.handle_message.call_args.args[0].source.user_id == "U_CI"


@pytest.mark.asyncio
async def test_selected_event_still_deduplicates(plugin_home):
    install_selector(plugin_home)
    adapter = make_adapter()
    await adapter._handle_slack_message(event())
    await adapter._handle_slack_message(event())
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_failure_drops_only_current_event(plugin_home):
    install_selector(plugin_home,
                     "import json; return 'select' if json.loads(event_json)['text'] == 'good' else None")
    adapter = make_adapter()
    await adapter._handle_slack_message(event())
    await adapter._handle_slack_message(event(text="good", ts="1700000000.002"))
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_callback_is_awaited(plugin_home, monkeypatch):
    install_selector(plugin_home, async_callback=True)
    monkeypatch.setattr(plugins, '_resolve_hook_callback_timeout', lambda: 0)
    adapter = make_adapter()
    await adapter._handle_slack_message(event())
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_callback_timeout_drops_eligible_event(plugin_home, monkeypatch):
    install_selector(plugin_home, "import asyncio; await asyncio.Event().wait()", async_callback=True)
    monkeypatch.setattr(plugins, '_resolve_hook_callback_timeout', lambda: 0.01)
    adapter = make_adapter()
    adapter._resolve_user_is_bot = AsyncMock(return_value=False)
    await adapter._handle_slack_message(event(subtype=None, bot_id=None, text='<@U_SELF> hi'))
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('last', ['skip', None, 'delegate'])
async def test_later_veto_overrides_earlier_select(plugin_home, last):
    install_selector(plugin_home)
    path = plugin_home / 'plugins' / 'selection-test' / '__init__.py'
    path.write_text("def register(ctx):\n"
                    "    ctx.register_hook('pre_platform_message', lambda event_json: 'select')\n"
                    f"    ctx.register_hook('pre_platform_message', lambda event_json: {last!r})\n")
    adapter = make_adapter()
    await adapter._handle_slack_message(event())
    assert adapter.handle_message.await_count == (1 if last == 'delegate' else 0)
