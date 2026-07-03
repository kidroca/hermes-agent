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
    from agent import turn_finalizer

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
    )
    monkeypatch.setattr(conversation_loop, "build_turn_context", lambda *a, **k: ctx)

    captured = {}

    def fake_finalize_turn(agent, **kwargs):
        captured.update(kwargs)
        return {"final_response": kwargs["final_response"]}

    monkeypatch.setattr(turn_finalizer, "finalize_turn", fake_finalize_turn)

    result = conversation_loop.run_conversation(_FakeAgent(), "hello")

    assert result == {"final_response": None}
    assert captured["memory_context"] == "## Hindsight\nPeter likes compact output."
