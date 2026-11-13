"""Profile-bound, fail-closed selection before a platform's eligibility gates.

Selection is not authorization. Adapters must retain their native access checks.
"""
from __future__ import annotations

import asyncio
import contextvars
import inspect
import json
import logging

from hermes_constants import get_hermes_home, set_hermes_home_override

logger = logging.getLogger(__name__)
HOOK = "pre_platform_message"


def bind_inbound_selector(platform: str):
    """Bind selection to the receiving adapter's construction scope, not a later turn.

    Payload strings are immutable and contain no SDK client or transport credentials.
    This intentionally selects from the transport owner's plugins, before profile routing.
    """
    context = contextvars.copy_context()
    home = str(get_hermes_home())
    context.run(set_hermes_home_override, home)

    async def select(event: dict, *, team_id: str = "", bot_user_id: str = "") -> str:
        payload = dict(platform=platform, profile_home=home, team_id=team_id,
                       bot_user_id=bot_user_id, event_json=json.dumps(event, allow_nan=False))
        return await asyncio.create_task(_select(payload), context=context.copy())

    return select


async def _select(payload: dict) -> str:
    # The normal observer dispatcher discards None/errors: that is unsafe for this gate.
    from hermes_cli.plugins import _delivery_manager, _resolve_hook_callback_timeout

    try:
        manager = _delivery_manager()
        decision = "delegate"
        for callback in manager.iter_hook_callbacks(HOOK):
            result = callback(**manager._hook_callback_kwargs(callback, payload))
            if inspect.isawaitable(result):
                timeout = _resolve_hook_callback_timeout()
                result = await asyncio.wait_for(result, timeout=timeout if timeout > 0 else None)
            if not isinstance(result, str) or result not in {"delegate", "skip", "select"}:
                logger.warning("%s returned an invalid decision; dropping event", HOOK)
                return "skip"
            if result == "skip":
                return "skip"
            if result == "select":
                decision = result
        return decision
    except (Exception, SystemExit) as exc:  # health: allow BLE001 -- plugin gate must fail closed, unlike observer hooks
        logger.warning("%s failed (%s); dropping event", HOOK, type(exc).__name__)
        return "skip"
