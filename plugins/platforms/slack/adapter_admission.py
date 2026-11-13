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
        team_id = self._event_team_id(event, payload, install_set=getattr(self, "_team_clients", None))
        if getattr(self, "_team_clients", None) and not team_id:
            logger.info("[Slack] Ignoring event with no authenticated workspace: type=%s channel=%s",
                        event.get("type"), event.get("channel", ""))
            return None
        if event_ts and self._dedup.is_duplicate(self._workspace_event_id(team_id, event_ts)):
            return None
        channel_id = event.get("channel", "")
        if self._is_ignored_channel(channel_id):
            logger.info("[Slack] Ignoring message in configured ignored channel %s", channel_id)
            return None
        if self._reject_foreign_dm(event, team_id, channel_id):
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

    def _reject_foreign_dm(self, event: dict, team_id: str, channel_id: str) -> bool:
        """Keep Slack Connect and synthetic-reaction DM boundaries ahead of selection."""
        # Bolt may put an enterprise E… id here; only a T… workspace identifies the author.
        author_team = ""
        for field in ("user_team", "team"):
            value = event.get(field)
            if isinstance(value, str) and value.startswith("T"):
                author_team = value
                break
        is_dm_event = (
            event.get("channel_type") == "im" or str(channel_id).startswith("D")
            or str(event.get("_hermes_reaction_source_channel", "")).startswith("D"))
        if is_dm_event and self._is_foreign_author(author_team, team_id):
            logger.info(
                "[Slack] Ignoring DM from external-org user %s (team %s) in %s",
                event.get("user"), author_team, channel_id)
            return True
        return False

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
