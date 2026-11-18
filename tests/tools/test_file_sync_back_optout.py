"""``terminal.sync_back: false`` skips the teardown download (a persistent SSH host keeps
its files; the whole remote tree was downloaded to apply a handful of changes).

The setting is read when the manager is created. The gateway serves profiles by switching
HERMES_HOME per turn, and teardown runs on the idle-cleanup thread outside any turn, where
``load_config()`` would return the default profile's config instead of the session's.
"""

import tarfile
from unittest.mock import MagicMock

import pytest

import hermes_cli.config as hermes_config

from tools.environments import file_sync
from tools.environments.file_sync import FileSyncManager


def _files(tmp_path, **contents):
    pairs = []
    for name, text in contents.items():
        host = tmp_path / name
        host.write_bytes(text.encode())
        pairs.append((str(host), f"/remote/.hermes/{name}"))
    return pairs


def _download(dest):
    with tarfile.open(dest, "w"):
        pass


@pytest.fixture
def make_pushed_manager(tmp_path):
    def make():
        pairs = _files(tmp_path, a="a")
        mgr = FileSyncManager(lambda: pairs, MagicMock(), MagicMock(), bulk_upload_fn=MagicMock(),
                              bulk_download_fn=MagicMock(side_effect=_download))
        mgr.sync(force=True)
        return mgr

    return make


def _config(monkeypatch, terminal):
    monkeypatch.setattr(hermes_config, "load_config", lambda: {"terminal": terminal})


@pytest.mark.parametrize("value", [False, "false", "off", 0])
def test_sync_back_can_be_disabled(make_pushed_manager, monkeypatch, tmp_path, value):
    _config(monkeypatch, {"sync_back": value})
    mgr = make_pushed_manager()
    mgr.sync_back(hermes_home=tmp_path)
    mgr._bulk_download_fn.assert_not_called()


@pytest.mark.parametrize("terminal", [{}, {"sync_back": True}, {"sync_back": None}])
def test_sync_back_stays_on_by_default(make_pushed_manager, monkeypatch, tmp_path, terminal):
    _config(monkeypatch, terminal)
    mgr = make_pushed_manager()
    mgr.sync_back(hermes_home=tmp_path)
    mgr._bulk_download_fn.assert_called_once()


def test_setting_is_taken_from_the_creating_profile_not_the_teardown_context(
        make_pushed_manager, monkeypatch, tmp_path):
    _config(monkeypatch, {"sync_back": False})   # lad-studio turn creates the environment
    mgr = make_pushed_manager()
    _config(monkeypatch, {})                     # cleanup thread sees the default profile
    mgr.sync_back(hermes_home=tmp_path)
    mgr._bulk_download_fn.assert_not_called()


def test_unreadable_config_keeps_sync_back_on(make_pushed_manager, monkeypatch, tmp_path):
    def broken():
        raise ValueError("bad yaml")

    monkeypatch.setattr(hermes_config, "load_config", broken)
    monkeypatch.setattr(file_sync.time, "sleep", lambda s: None)
    mgr = make_pushed_manager()
    mgr.sync_back(hermes_home=tmp_path)
    # Still attempted (the extraction cap read also fails here and drives the existing retries).
    mgr._bulk_download_fn.assert_called()
