"""Canonical ancestry is advisory, never the fork's installable update target."""
import os
import subprocess

import pytest

from hermes_cli import banner
from hermes_cli.source_releases import source_repository


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "test")
    git("config", "user.email", "test@example.invalid")
    git("commit", "--allow-empty", "-qm", "base")
    base = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "-qm", "canonical")
    upstream = git("rev-parse", "HEAD")
    git("checkout", "--detach", base)
    git("commit", "--allow-empty", "-qm", "carried")
    head = git("rev-parse", "HEAD")
    git("remote", "add", "origin", "https://github.com/example/fork.git")
    git("remote", "add", "upstream", "https://example.invalid/not-canonical.git")
    git("update-ref", "refs/remotes/origin/main", head)
    monkeypatch.setattr(banner, "_resolve_repo_dir", lambda: repo)
    return repo, git, upstream, head


@pytest.mark.parametrize("url", [
    "https://github.com/NousResearch/hermes-agent.git",
    "git@github.com:NousResearch/hermes-agent.git",
    "ssh://git@github.com/NousResearch/hermes-agent.git",
])
def test_canonical_ancestry_is_separate_from_fork_update_source(checkout, monkeypatch, capsys, url):
    repo, git, upstream, head = checkout
    git("remote", "add", "vendor", url)
    git("update-ref", "refs/remotes/vendor/main", upstream)
    real_run = subprocess.run

    def read_only(args, **kw):
        assert not any(arg in {"fetch", "ls-remote", "pull"} for arg in args)
        return real_run(args, **kw)

    monkeypatch.setattr(subprocess, "run", read_only)
    state = banner.get_git_banner_state(repo)
    assert state["upstream"] == upstream[:8]
    assert state["local"] == head[:8]
    assert state["ahead"] == state["behind"] == 1
    text = banner.format_git_status(state)
    assert "canonical upstream" in text and "1 behind" in text
    assert "1 carried commit" in text and "local refs" in text
    assert "hermes update" not in text
    assert source_repository(["git"], repo) == "example/fork"
    from types import SimpleNamespace
    from hermes_cli import status
    monkeypatch.setattr(status, "PROJECT_ROOT", repo)
    monkeypatch.setattr(status, "_effective_provider_label", lambda: "test")
    status._render_environment(SimpleNamespace())
    assert text in capsys.readouterr().out
    monkeypatch.setattr("hermes_cli.config.get_project_root", lambda: repo)
    monkeypatch.setattr("hermes_cli.update_channel.resolve_update_channel", lambda *a: "main")
    monkeypatch.setattr(banner, "_git_banner_state_cache", None)
    assert text in banner.format_banner_version_label()


@pytest.mark.parametrize("missing", ["remote", "ref", "history"])
def test_unavailable_canonical_history_is_not_reported_current(checkout, missing):
    repo, git, upstream, head = checkout
    if missing != "remote":
        git("remote", "add", "vendor", "https://github.com/NousResearch/hermes-agent.git")
    if missing == "history":
        git("update-ref", "refs/remotes/vendor/main", upstream)
        (repo / ".git" / "shallow").write_text(head + "\n")
    state = banner.get_git_banner_state(repo)
    text = banner.format_git_status(state)
    assert "unknown" in text
    assert head[:8] in text
    assert "0 behind" not in text
    assert "0 carried" not in text
