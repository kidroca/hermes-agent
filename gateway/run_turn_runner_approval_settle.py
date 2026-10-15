"""Host-owned approval settlement for messaging platforms.

Retire adapter-owned exact approval views on every outcome. Other adapters keep
the existing timeout notice. Failed UI edits cannot change the host decision;
a missing registration means unknown outcome, never inferred execution.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from agent.i18n import t
from gateway.platforms.base_exec_approval import approval_timeout_seconds, format_approval_timed_out_notice

logger = logging.getLogger(__name__)


def register_timeout_notice(
    runner, approval_data: dict, *, command: str, card_message_id: Optional[str]) -> None:
    """Arm a settle hook that posts the timed-out notice for ``approval_data['request_id']``.

    ``runner`` is the ``TurnRunner`` (for ``_ctx`` and ``_schedule``); ``card_message_id`` is the
    delivered BUTTON card's id when the adapter returned one, so the card itself is edited in place
    (which also drops its buttons). The plain-text prompt passes ``None``: it has no buttons to
    drop and rewriting it would erase the record of what was asked. ``command`` is the
    already-redacted command shown to the user. The notice is skipped when the run is no longer
    current (``ctx._run_still_current``).
    """
    from tools.approval import register_gateway_settle

    request_id = approval_data.get("request_id")
    session_key = runner._ctx.session_key or ""
    if not request_id or not session_key:
        return
    timeout_s = approval_timeout_seconds()

    adapter = getattr(runner._ctx, "_status_adapter", None)
    retire = getattr(type(adapter), "retire_exec_approval", None)

    def settle(reason: str) -> None:
        if retire is not None:
            runner._schedule(
                retire(adapter, session_key, request_id, reason),
                "Approval retirement scheduling error")
            return
        if reason != "timeout":
            return  # answered / interrupted / notify_failed already produced their own feedback
        # Same guard as every other late notice in TurnRunner: after /stop, /new or a restart the
        # turn is over and this chat belongs to a newer run — do not edit or post into it.
        still_current = getattr(runner._ctx, "_run_still_current", None)
        if callable(still_current) and not still_current():
            return
        runner._schedule(
            _post_timeout_notice(runner._ctx, command, card_message_id, timeout_s),
            "Approval timeout notice scheduling error")

    registered = register_gateway_settle(session_key, request_id, settle)
    if registered is False and retire is not None:
        settle("unknown")


async def _post_timeout_notice(ctx, command: str, card_message_id: Optional[str], timeout_s: int) -> None:
    from gateway.run import _interim_metadata

    adapter = ctx._status_adapter
    notice = format_approval_timed_out_notice(timeout_s)
    metadata = _interim_metadata(ctx._status_thread_metadata)
    try:
        # Plain markdown, not the card's platform markup: ``edit_message`` re-formats it itself.
        if card_message_id and await _edit_card(
                adapter, ctx._status_chat_id, card_message_id,
                t("gateway.exec_approval.timed_out_card_body", notice=notice, command=command)):
            return
        await adapter.send(ctx._status_chat_id, notice, metadata=metadata)
    except Exception:
        logger.debug("Approval timeout notice failed", exc_info=True)


async def _edit_card(adapter, chat_id: str, message_id: str, content: str) -> bool:
    """Edit the card in place (drops the buttons on platforms whose edit replaces the markup)."""
    edit: Optional[Callable[..., Any]] = getattr(adapter, "edit_message", None)
    if edit is None:
        return False
    try:
        result = await edit(chat_id, message_id, content)
    except Exception:
        logger.debug("Approval card edit failed; sending the notice as a new message", exc_info=True)
        return False
    return bool(getattr(result, "success", False))


def register_after_ambiguous_send(runner, approval_data: dict, *, command: str, future) -> None:
    """Late send acknowledgements retain owner scope and retire stale exact cards.

    No second send, no inferred verdict when registration loses to settlement.
    """
    from contextvars import copy_context
    scope = copy_context()

    def delivered(done):
        try:
            result = done.result()
        except Exception:
            logger.debug("Ambiguous approval send did not complete", exc_info=True)
            return
        if getattr(result, "success", False):
            scope.run(register_timeout_notice, runner, approval_data, command=command,
                      card_message_id=getattr(result, "message_id", None))

    future.add_done_callback(delivered)
