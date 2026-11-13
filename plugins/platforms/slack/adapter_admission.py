"""Early selection for Slack messages; native authorization stays downstream."""
import logging

logger = logging.getLogger(f"{__package__}.adapter" if __package__ else "adapter")


def _log_received(event: dict) -> None:
    # Metadata only, before filters: distinguish dropped events from missing subscriptions.
    profile = event.get("bot_profile") or {}
    logger.debug(
        "[Slack] event received type=%s subtype=%s user=%s bot_id=%s bot_name=%s "
        "channel=%s ts=%s thread_ts=%s", event.get("type"), event.get("subtype"),
        event.get("user", "") or "", event.get("bot_id", "") or "",
        (profile.get("name") if isinstance(profile, dict) else "") or "",
        event.get("channel", ""), event.get("ts", ""), event.get("thread_ts", ""))


class SlackAdmissionMixin:
    async def _prefilter_inbound(self, event: dict, payload):
        """Normalize edits and return (event, team, channel, selected), or drop.

        Selection cannot defeat replay, ignored-channel, subtype or self-echo guards.
        """
        if logger.isEnabledFor(logging.DEBUG):
            _log_received(event)
        if event.get("subtype") == "message_changed":
            event = self._normalize_changed_message(event)
            if event is None:
                return None
        event_ts = event.get("_slack_changed_event_ts") or event.get("ts", "")
        team_id = self._event_team_id(event, payload)
        if event_ts and self._dedup.is_duplicate(self._workspace_event_id(team_id, event_ts)):
            return None
        channel_id = event.get("channel", "")
        if self._is_ignored_channel(channel_id):
            logger.info("[Slack] Ignoring message in configured ignored channel %s", channel_id)
            return None
        selector = getattr(self, "_inbound_selector", None)
        decision = "delegate"
        if selector is not None:
            bot_uid = self._team_bot_user_ids.get(team_id, self._bot_user_id) or ""
            decision = await selector(event, team_id=team_id, bot_user_id=bot_uid)
        if decision == "skip":
            return None
        selected = decision == "select"
        if selected:
            if self._selection_is_own_message(event, team_id):
                return None
        elif await self._drop_bot_sender(event):
            return None
        # Only conversational subtypes may start turns, including on free-response channels.
        if event.get("subtype") not in (
            None, "", "file_share", "thread_broadcast", "me_message",
            "bot_message", "document_mention",
        ):
            logger.debug("[Slack] Dropping non-conversational message subtype=%s in channel %s",
                         event.get("subtype"), channel_id)
            return None
        return event, team_id, channel_id, selected

    def _selection_is_own_message(self, event: dict, team_id: str) -> bool:
        bot_users = self._team_bot_user_ids
        bot_ids = getattr(self, "_team_bot_ids", {})
        own_users = {bot_users.get(team_id, self._bot_user_id)} if team_id else set(bot_users.values()) | {self._bot_user_id}
        own_bots = {bot_ids.get(team_id)} if team_id else set(bot_ids.values())
        own_users -= {None, ""}
        own_bots -= {None, ""}
        profile = event.get("bot_profile") or {}
        if not isinstance(profile, dict):
            return True
        return bool(
            event.get("user") in own_users or profile.get("user_id") in own_users
            or event.get("bot_id") in own_bots or profile.get("id") in own_bots)
