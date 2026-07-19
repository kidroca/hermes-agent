from types import SimpleNamespace


class _IterationBudget:
    remaining = 0


class _FakeAgent:
    api_mode = "chat"
    max_iterations = 0
    iteration_budget = _IterationBudget()
    _budget_grace_call = False


def test_prefetched_memory_context_reaches_turn_finalizer(monkeypatch):
    from agent import conversation_loop

    ctx = SimpleNamespace(
        user_message="hello",
        original_user_message="hello",
        messages=[{"role": "user", "content": "hello"}],
        conversation_history=[],
        active_system_prompt="",
        effective_task_id="task-id",
        turn_id="turn-id",
        current_turn_user_idx=0,
        should_review_memory=False,
        plugin_user_context="",
        ext_prefetch_cache="## Hindsight\nPeter likes compact output.",
        preflight_compression_blocked=False,
    )
    monkeypatch.setattr(conversation_loop, "build_turn_context", lambda *a, **k: ctx)

    captured = {}

    def fake_finalize_turn(agent, **kwargs):
        captured.update(kwargs)
        return {"final_response": kwargs["final_response"]}

    monkeypatch.setattr(conversation_loop, "finalize_turn", fake_finalize_turn)

    result = conversation_loop.run_conversation(
        _FakeAgent(), "hello", memory_query_message="memory-only query"
    )

    assert result == {"final_response": None}
    assert captured["memory_context"] == "## Hindsight\nPeter likes compact output."
    assert captured["memory_query_message"] == "memory-only query"
