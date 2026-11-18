"""Skill-manager discovery through external category symlinks uses real filesystem I/O."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agent import skill_utils
from tools import skill_manager_tool, skills_tool
from tools.registry import registry


@pytest.fixture
def external_view(tmp_path, monkeypatch):
    home = tmp_path / "home"
    local = home / "skills"
    local.mkdir(parents=True)
    view = tmp_path / "view"
    view.mkdir()
    category = tmp_path / "pool" / "development"
    category.mkdir(parents=True)
    (view / "development").symlink_to(category, target_is_directory=True)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(skill_manager_tool, "SKILLS_DIR", local)
    monkeypatch.setattr(skills_tool, "SKILLS_DIR", local)
    (home / "config.yaml").write_text(
        f"skills:\n  external_dirs:\n    - {view}\n", encoding="utf-8"
    )
    skill_utils._raw_config_cache_clear()
    skill_utils._external_dirs_cache_clear()
    yield local, view, category
    skill_utils._raw_config_cache_clear()
    skill_utils._external_dirs_cache_clear()


def _write_skill(directory, name="shared-guide"):
    directory.mkdir(parents=True)
    skill_md = directory / "SKILL.md"
    skill_md.write_text(
        f"---\nname: {name}\ndescription: Use when testing linked skills.\n---\n\n"
        "# Guide\n\nOriginal instructions.\n",
        encoding="utf-8",
    )
    return skill_md


def _manage(action, name, **kwargs):
    result = registry.dispatch("skill_manage", {
        "operations": [{"action": action, "name": name, **kwargs}],
    })
    assert isinstance(result, str)
    return json.loads(result)


@pytest.mark.platforms("posix")
@pytest.mark.parametrize("name", ["linked-guide", "shared-guide"])
def test_patch_external_category_symlink_in_place(external_view, name):
    local, view, category = external_view
    skill_md = _write_skill(category / "linked-guide")
    assert json.loads(skills_tool.skill_view(name))["success"]

    result = _manage(
        "patch", name, old_string="Original instructions.", new_string="Updated instructions."
    )

    assert result["success"], result
    assert "Updated instructions." in skill_md.read_text(encoding="utf-8")
    assert (view / "development").is_symlink()
    assert not (local / "linked-guide").exists()


@pytest.mark.platforms("posix")
def test_linked_discovery_keeps_local_precedence_and_exclusions(external_view, monkeypatch):
    local, view, category = external_view
    external_md = _write_skill(category / "linked-guide")
    # Force the adversarial traversal order without replacing filesystem discovery.
    walk = os.walk

    def archive_first(*args, **kwargs):
        for directory, dirs, files in walk(*args, **kwargs):
            dirs.sort()
            yield directory, dirs, files

    monkeypatch.setattr(os, "walk", archive_first)
    # Visit the archived alias first: it must not consume the real-path identity.
    hidden_root = view / ".archive"
    hidden_root.symlink_to(category, target_is_directory=True)
    found = skill_manager_tool._find_skill("linked-guide")
    assert found is not None
    assert found["path"] == view / "development" / "linked-guide"
    local_md = _write_skill(local / "linked-guide")
    _write_skill(category / ".archive" / "archived-guide")
    _write_skill(category / "linked-guide" / "references" / "support-guide")

    assert skill_manager_tool._find_skill("archived-guide") is None
    assert skill_manager_tool._find_skill("support-guide") is None
    assert list(skill_manager_tool._iter_skill_dirs(hidden_root)) == []
    result = _manage(
        "patch", "linked-guide",
        old_string="Original instructions.", new_string="Local instructions."
    )
    assert result["success"], result
    assert "Local instructions." in local_md.read_text(encoding="utf-8")
    assert "Original instructions." in external_md.read_text(encoding="utf-8")


@pytest.mark.platforms("posix")
def test_delete_through_category_symlink_still_refuses_out_of_root_target(external_view):
    _, _, category = external_view
    skill_md = _write_skill(category / "linked-guide")

    result = _manage("delete", "linked-guide")

    assert not result["success"], result
    assert "does not resolve inside any known skills root" in result["error"]
    assert skill_md.is_file()


@pytest.mark.platforms("posix")
def test_linked_discovery_bounds_branching_symlink_cycles(external_view):
    _, view, category = external_view
    _write_skill(category / "linked-guide")
    for name in ("loop-a", "loop-b"):
        (category / name).symlink_to(view, target_is_directory=True)

    # A child deadline bounds even an eager scanner's exponential cycle traversal.
    result = subprocess.run(
        [sys.executable, "-c", (
            "import json, sys; from pathlib import Path; "
            "from tools.skill_manager_tool import _iter_skill_dirs; "
            "print(json.dumps([p.name for p in _iter_skill_dirs(Path(sys.argv[1]))]))"
        ), str(view)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True, text=True, timeout=10, check=True,
    )
    assert json.loads(result.stdout) == ["linked-guide"]
