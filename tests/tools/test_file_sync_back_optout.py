"""``terminal.sync_back: false`` skips the teardown download (a persistent SSH host keeps
its files; the whole remote tree was downloaded to apply a handful of changes)."""


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


@pytest.fixture
def pushed_manager(tmp_path):
    def download(dest):
        with tarfile.open(dest, "w"):
            pass

    pairs = _files(tmp_path, a="a")
    mgr = FileSyncManager(lambda: pairs, MagicMock(), MagicMock(), bulk_upload_fn=MagicMock(),
                          bulk_download_fn=MagicMock(side_effect=download))
    mgr.sync(force=True)
    return mgr


@pytest.mark.parametrize("value", [False, "false", "off", 0])
def test_sync_back_can_be_disabled(pushed_manager, monkeypatch, tmp_path, value):
    monkeypatch.setattr(hermes_config, "load_config", lambda: {"terminal": {"sync_back": value}})
    pushed_manager.sync_back(hermes_home=tmp_path)
    pushed_manager._bulk_download_fn.assert_not_called()


@pytest.mark.parametrize("terminal", [{}, {"sync_back": True}, {"sync_back": None}])
def test_sync_back_stays_on_by_default(pushed_manager, monkeypatch, tmp_path, terminal):
    monkeypatch.setattr(hermes_config, "load_config", lambda: {"terminal": terminal})
    pushed_manager.sync_back(hermes_home=tmp_path)
    pushed_manager._bulk_download_fn.assert_called_once()


def test_unreadable_config_keeps_sync_back_on(pushed_manager, monkeypatch, tmp_path):
    def broken():
        raise ValueError("bad yaml")

    monkeypatch.setattr(hermes_config, "load_config", broken)
    monkeypatch.setattr(file_sync.time, "sleep", lambda s: None)
    pushed_manager.sync_back(hermes_home=tmp_path)
    # Still attempted (the extraction cap read also fails here and drives the existing retries).
    pushed_manager._bulk_download_fn.assert_called()
