"""Exact-request Discord approval lifecycle; the generic view stays unchanged."""
import logging

import discord
from agent.i18n import t
from gateway.config import Platform
from gateway.platforms.base import unauthorized_action_notice

logger = logging.getLogger(__name__)


class ExecApprovalLifecycle:
    def close_controls(self):
        self.resolved = True
        self._disable_all()
        self.stop()
        if self._detach is not None:
            detach, self._detach = self._detach, None
            detach()


    async def settle_from_owner(self, reason: str):
        was_resolved = self.resolved
        self.close_controls()
        if was_resolved:
            return
        key = {
            "resolved": "platform.discord.approval.settled_elsewhere",
            "timeout": "platform.discord.approval.owner_timeout",
        }.get(reason, "platform.discord.approval.outcome_unknown")
        self._owner_footer = t(key)
        await self._expire_embed(self._owner_footer)


    async def on_timeout(self):
        # The view timer is not the authoritative waiter deadline. It cannot
        # infer whether a peer committed a choice before its callback arrived.
        await self.settle_from_owner("unknown")


    def _check_auth(self, interaction: discord.Interaction) -> bool:
        """Base admission always required; with ``require_admin`` the clicker must
        also be an admin. Fails closed (logged once) when no admins are configured."""
        if not super()._check_auth(interaction):
            return False
        if not self.require_admin:
            return True
        user = getattr(interaction, "user", None)
        try:
            uid = str(getattr(user, "id", "") or "")
        except Exception:
            logger.debug("Discord approval user identity unavailable", exc_info=True)
            uid = ""
        if uid and uid in self.admin_user_ids:
            return True
        if not self.admin_user_ids:
            logger.warning(
                "[Discord] require_admin_for_exec_approval is enabled but "
                "no admins are configured (allow_admin_from is empty) — "
                "exec approval buttons are disabled for everyone. Add "
                "admin user IDs under the discord platform's "
                "allow_admin_from, or disable the toggle."
            )
        return False


    async def _resolve(self, interaction: discord.Interaction, choice: str, color: discord.Color, label_key: str):
        """Resolve the approval via the gateway approval queue and update the embed."""
        if not await self._gate(
            interaction, resolved_msg=t("platform.discord.approval.already_resolved"),
            unauth_msg=unauthorized_action_notice(Platform.DISCORD),
        ):
            return
        label = t(label_key)
        self.close_controls()
        # Resolve before editing; an expired request must not claim "Approved".
        try:
            from tools.approval import resolve_gateway_approval
            # Old or incomplete cards must never fall back to the session's FIFO head.
            count = resolve_gateway_approval(self.session_key, choice, request_id=self.request_id) if self.request_id else 0
            logger.info(
                "Discord button resolved %d approval(s) for session %s (choice=%s, user=%s)",
                count, self.session_key, choice, interaction.user.display_name)
        except Exception as exc:
            logger.error("Failed to resolve gateway approval from button: %s", exc, exc_info=True)
            count = 0
        if not count:
            color = discord.Color.dark_grey()
            label = t("platform.discord.approval.outcome_unknown")
        await self._finalize_embed(
            interaction, color,
            t("platform.discord.approval.by_user", label=label, user=interaction.user.display_name) if count else label)
