from types import SimpleNamespace

from plugins.memory.hindsight import _format_recall_result, _recall_source_label


def test_recall_source_label_prefers_profile_tag():
    result = SimpleNamespace(
        metadata={"agent_identity": "coding", "source": "hermes-coding"},
        tags=["personal-memory", "profile:lawyer"],
        text="Legal note",
    )

    assert _recall_source_label(result) == "profile:lawyer"


def test_recall_source_label_falls_back_to_metadata_agent_identity():
    result = SimpleNamespace(metadata={"agent_identity": "coding"}, tags=[], text="Build note")

    assert _recall_source_label(result) == "profile:coding"


def test_recall_source_label_derives_profile_from_retain_source():
    result = SimpleNamespace(metadata={"source": "hermes-lad-studio"}, tags=[], text="Studio note")

    assert _recall_source_label(result) == "profile:lad-studio"


def test_recall_source_label_does_not_claim_profile_when_unknown():
    result = SimpleNamespace(metadata={}, tags=[], text="Plain memory")

    assert _recall_source_label(result) == "source:unknown"


def test_format_recall_result_prefixes_memory_with_profile_source():
    result = SimpleNamespace(tags=["session:abc", "profile:default"], text="Peter prefers concise output.")

    assert _format_recall_result(result) == "- profile:default: Peter prefers concise output."
    assert _format_recall_result(result, index=2) == "2. profile:default: Peter prefers concise output."


def test_format_recall_result_skips_empty_text():
    result = SimpleNamespace(tags=["profile:default"], text="   ")

    assert _format_recall_result(result) == ""
