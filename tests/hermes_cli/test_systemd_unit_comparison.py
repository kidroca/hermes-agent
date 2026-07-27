"""Regression tests for systemd unit staleness normalization."""

from __future__ import annotations


def test_path_only_difference_is_not_stale(tmp_path, monkeypatch):
    from hermes_cli import gateway as gw

    installed = """[Service]
ExecStart=/opt/hermes/venv/bin/python -m hermes_cli.main gateway run
Environment="PATH=/opt/hermes/venv/bin:/usr/bin:/bin"
Environment="HERMES_HOME=/home/peter/.hermes"
"""
    generated = """[Service]
ExecStart=/opt/hermes/venv/bin/python -m hermes_cli.main gateway run
Environment="PATH=/opt/hermes/venv/bin:/mnt/c/Android/sdk:/usr/bin:/bin"
Environment="HERMES_HOME=/home/peter/.hermes"
"""
    unit_file = tmp_path / "hermes-gateway.service"
    unit_file.write_text(installed)
    monkeypatch.setattr(gw, "get_systemd_unit_path", lambda system=False: unit_file)
    monkeypatch.setattr(
        gw,
        "generate_systemd_unit",
        lambda system=False, run_as_user=None: generated,
    )

    assert gw.systemd_unit_is_current(system=False) is True


def test_non_wsl_path_difference_remains_stale():
    from hermes_cli.gateway import _normalize_systemd_unit_for_comparison

    installed = """[Service]
Environment="PATH=/opt/node-v20/bin:/mnt/c/WINDOWS/system32:/usr/bin"
"""
    generated = """[Service]
Environment="PATH=/opt/node-v22/bin:/mnt/c/WINDOWS/system32:/usr/bin"
"""

    assert _normalize_systemd_unit_for_comparison(
        installed
    ) != _normalize_systemd_unit_for_comparison(generated)


def test_non_drive_mnt_path_difference_remains_stale():
    from hermes_cli.gateway import _normalize_systemd_unit_for_comparison

    installed = """[Service]
Environment="PATH=/usr/bin"
"""
    generated = """[Service]
Environment="PATH=/mnt/tools/bin:/usr/bin"
"""

    assert _normalize_systemd_unit_for_comparison(
        installed
    ) != _normalize_systemd_unit_for_comparison(generated)


def test_non_path_environment_difference_remains_stale():
    from hermes_cli.gateway import _normalize_systemd_unit_for_comparison

    installed = """[Service]
Environment="PATH=/usr/bin:/bin"
Environment="HERMES_HOME=/home/peter/.hermes"
"""
    generated = """[Service]
Environment="PATH=/opt/hermes/bin:/usr/bin:/bin"
Environment="HERMES_HOME=/home/other/.hermes"
"""

    assert _normalize_systemd_unit_for_comparison(
        installed
    ) != _normalize_systemd_unit_for_comparison(generated)


def test_combined_environment_assignments_are_not_hidden():
    from hermes_cli.gateway import _normalize_systemd_unit_for_comparison

    installed = (
        '[Service]\nEnvironment="PATH=/usr/bin:/bin" '
        '"HERMES_HOME=/home/peter/.hermes"\n'
    )
    generated = (
        '[Service]\nEnvironment="PATH=/opt/hermes/bin:/usr/bin:/bin" '
        '"HERMES_HOME=/home/other/.hermes"\n'
    )

    assert _normalize_systemd_unit_for_comparison(
        installed
    ) != _normalize_systemd_unit_for_comparison(generated)


def test_non_path_directive_difference_remains_stale():
    from hermes_cli.gateway import _normalize_systemd_unit_for_comparison

    installed = """[Service]
ExecStart=/opt/hermes/venv/bin/python -m hermes_cli.main gateway run
Environment="PATH=/usr/bin:/bin"
"""
    generated = """[Service]
ExecStart=/opt/hermes/venv/bin/python -m hermes_cli.main gateway status
Environment="PATH=/opt/hermes/bin:/usr/bin:/bin"
"""

    assert _normalize_systemd_unit_for_comparison(
        installed
    ) != _normalize_systemd_unit_for_comparison(generated)
