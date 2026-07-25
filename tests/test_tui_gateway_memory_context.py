import threading

from tui_gateway import server


def _session(agent=None, **extra):
    return {
        "agent": agent,
        "session_key": "session-key",
        "history": [],
        "history_lock": threading.Lock(),
        "history_version": 0,
        "running": False,
        "attached_images": [],
        "image_counter": 0,
        "cols": 80,
        "slash_worker": None,
        "show_reasoning": False,
        "tool_progress_mode": "all",
        **extra,
    }


def test_prompt_submit_emits_memory_context_when_tui_display_enabled(monkeypatch):
    class _Agent:
        def run_conversation(
            self,
            prompt,
            conversation_history=None,
            stream_callback=None,
            persist_user_message=None,
            **_kwargs,
        ):
            return {
                "final_response": "reply",
                "memory_context": "## Hindsight\nPeter likes compact output.",
                "messages": [{"role": "assistant", "content": "reply"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            assert self._target is not None
            self._target()

    server._sessions["sid"] = _session(agent=_Agent())
    emits: list[tuple] = []
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a, _m=None: {})
        monkeypatch.setattr(server, "_load_cfg", lambda: {"display": {"tui_memory_context": True}})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: emits.append(a))

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
        assert resp is not None
        assert resp.get("result")

        complete_calls = [a for a in emits if a[0] == "message.complete"]
        assert len(complete_calls) == 1
        _, _, payload = complete_calls[0]
        assert payload["memory_context"] == "## Hindsight\nPeter likes compact output."
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_emits_memory_context_before_streaming(monkeypatch):
    class _Agent:
        def run_conversation(
            self,
            prompt,
            conversation_history=None,
            stream_callback=None,
            persist_user_message=None,
            memory_context_callback=None,
            **_kwargs,
        ):
            assert memory_context_callback is not None
            cb = memory_context_callback
            cb("## Hindsight\nPeter likes compact output.")
            stream_callback("reply")
            return {
                "final_response": "reply",
                "memory_context": "## Hindsight\nPeter likes compact output.",
                "messages": [{"role": "assistant", "content": "reply"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            assert self._target is not None
            self._target()

    server._sessions["sid"] = _session(agent=_Agent())
    emits: list[tuple] = []
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a, _m=None: {})
        monkeypatch.setattr(server, "_load_cfg", lambda: {"display": {"tui_memory_context": True}})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: emits.append(a))

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
        assert resp is not None
        assert resp.get("result")

        event_names = [a[0] for a in emits]
        assert event_names.index("memory_context.available") < event_names.index("message.delta")
        assert event_names.index("memory_context.available") < event_names.index("message.complete")

        complete_payload = [a for a in emits if a[0] == "message.complete"][0][2]
        assert "memory_context" not in complete_payload
    finally:
        server._sessions.pop("sid", None)
