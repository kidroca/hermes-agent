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


def test_recall_source_label_is_empty_when_no_provenance_exists():
    result = SimpleNamespace(metadata={}, tags=[], text="Plain memory")

    assert _recall_source_label(result) == ""


def test_format_recall_result_collapses_available_profile_and_session_provenance():
    result = SimpleNamespace(tags=["session:abc", "profile:default"], text="Peter prefers concise output.")

    assert _format_recall_result(result) == "- [profile:default · s:abc] Peter prefers concise output."
    assert _format_recall_result(result, index=2) == "2. [profile:default · s:abc] Peter prefers concise output."


def test_format_recall_result_omits_source_prefix_when_no_provenance_exists():
    result = SimpleNamespace(metadata={}, tags=[], text="Recovered memory")

    assert _format_recall_result(result) == "- Recovered memory"
    assert _format_recall_result(result, index=1) == "1. Recovered memory"


def test_format_recall_result_includes_compact_utc_timestamp_and_profile():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T21:48:08.061877+00:00",
        tags=["session:20260717_165728_c2438c", "profile:default"],
        text="Production Hindsight is now on BGE v2 M3.",
    )

    assert _format_recall_result(result) == (
        "- [2026-07-17 21:48Z · profile:default · s:c2438c] Production Hindsight is now on BGE v2 M3."
    )
    assert _format_recall_result(result, index=3) == (
        "3. [2026-07-17 21:48Z · profile:default · s:c2438c] Production Hindsight is now on BGE v2 M3."
    )


def test_format_recall_result_includes_all_session_tags_for_compact_provenance():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T21:48:08Z",
        tags=["session:20260717_165728_c2438c", "session:20260718_010203_otherid", "profile:default"],
        text="Timestamped memory.",
    )

    assert _format_recall_result(result) == (
        "- [2026-07-17 21:48Z · profile:default · s:c2438c · s:otherid] Timestamped memory."
    )


def test_format_recall_result_collapses_colliding_session_suffixes():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T21:48:08Z",
        tags=["session:alpha_c2438c", "session:beta_c2438c", "profile:default"],
        text="Colliding sessions.",
    )

    assert _format_recall_result(result) == (
        "- [2026-07-17 21:48Z · profile:default · s:c2438c] Colliding sessions."
    )


def test_format_recall_result_deduplicates_identical_full_session_tags():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T21:48:08Z",
        tags=["session:alpha_c2438c", "session:alpha_c2438c", "session:beta_otherid", "profile:default"],
        text="Repeated session.",
    )

    assert _format_recall_result(result) == (
        "- [2026-07-17 21:48Z · profile:default · s:c2438c · s:otherid] Repeated session."
    )


def test_format_recall_result_collapses_source_only_provenance():
    result = SimpleNamespace(metadata={"source": "external"}, tags=[], text="External memory.")

    assert _format_recall_result(result) == "- [source:external] External memory."


def test_format_recall_result_accepts_z_timestamp():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T21:48:08Z",
        tags=[],
        text="Timestamped memory.",
    )

    assert _format_recall_result(result) == "- [2026-07-17 21:48Z] Timestamped memory."


def test_format_recall_result_treats_naive_timestamp_as_utc():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T21:48:08",
        tags=[],
        text="Timestamped memory.",
    )

    assert _format_recall_result(result) == "- [2026-07-17 21:48Z] Timestamped memory."


def test_format_recall_result_normalizes_timestamp_offset_to_utc():
    result = SimpleNamespace(
        mentioned_at="2026-07-17T23:48:08+02:00",
        tags=[],
        text="Timestamped memory.",
    )

    assert _format_recall_result(result) == "- [2026-07-17 21:48Z] Timestamped memory."


def test_format_recall_result_falls_back_when_timestamp_is_malformed():
    result = SimpleNamespace(
        mentioned_at="not-a-timestamp",
        tags=["profile:default"],
        text="Recovered memory.",
    )

    assert _format_recall_result(result) == "- [profile:default] Recovered memory."


def test_format_recall_result_skips_empty_text():
    result = SimpleNamespace(tags=["profile:default"], text="   ")

    assert _format_recall_result(result) == ""
