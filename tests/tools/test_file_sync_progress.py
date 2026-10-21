"""Confirmed sync progress survives later transport failures."""

import hashlib
import io
import os
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tools.environments.file_sync import FileSyncManager


def sources(tmp_path, count=4):
    pairs = []
    for index in range(count):
        path = tmp_path / str(index)
        path.write_bytes(b"old!")
        pairs.append((str(path), f"/remote/{index}"))
    return pairs


@pytest.mark.parametrize("bulk", [False, True])
def test_later_upload_failure_retains_confirmed_progress(tmp_path, bulk):
    pairs = sources(tmp_path)
    calls = []

    def upload(files):
        calls.append([remote for _, remote in files])
        if len(calls) == 2:
            raise RuntimeError("transport failed")

    options = {"bulk_upload_fn": upload, "upload_batch_max_files": 2} if bulk else {}
    manager = FileSyncManager(lambda: pairs, lambda host, remote: upload([(host, remote)]), lambda paths: None,
                              **options)
    manager.sync(force=True)
    confirmed = set(calls[0])
    assert set(manager._pushed_hashes) == confirmed
    assert manager._last_sync_time == 0
    calls.clear()
    manager._bulk_upload_fn = (lambda files: calls.append([remote for _, remote in files])) if bulk else None
    manager._upload_fn = lambda host, remote: calls.append([remote])
    manager.sync()
    assert confirmed.isdisjoint(remote for batch in calls for remote in batch)
    assert {remote for batch in calls for remote in batch} == {remote for _, remote in pairs} - confirmed
    assert set(manager._pushed_hashes) == {remote for _, remote in pairs}


def test_delete_checkpoints_do_not_repeat_uploads_or_confirmed_deletes(tmp_path):
    pairs = sources(tmp_path)
    uploads, deletes = [], []

    def delete(paths):
        deletes.append(list(paths))
        if len(deletes) == 2:
            raise RuntimeError("delete failed")

    manager = FileSyncManager(lambda: pairs, lambda host, remote: uploads.append(remote), delete,
                              upload_batch_max_files=1)
    manager.sync(force=True)
    pairs[:] = pairs[-1:]
    Path(pairs[0][0]).write_bytes(b"new!")
    manager.sync(force=True)
    assert "/remote/0" not in manager._synced_files
    assert "/remote/1" in manager._synced_files
    uploads.clear()
    deletes.clear()
    manager._delete_fn = lambda paths: deletes.extend(paths)
    manager.sync(force=True)
    assert uploads == []
    assert deletes == ["/remote/1", "/remote/2"]


@pytest.mark.parametrize("during_upload", [False, True])
def test_same_size_same_mtime_edits_are_detected(tmp_path, during_upload):
    pairs = sources(tmp_path, 1)
    host = Path(pairs[0][0])
    stamp = host.stat()
    received = []

    def edit():
        host.write_bytes(b"new!")
        os.utime(host, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))

    def upload(source, remote):
        received.append(Path(source).read_bytes())
        if during_upload and len(received) == 1:
            edit()

    manager = FileSyncManager(lambda: pairs, upload, lambda paths: None)
    manager.sync(force=True)
    assert manager._pushed_hashes[pairs[0][1]] == hashlib.sha256(b"old!").hexdigest()
    if not during_upload:
        edit()
    manager.sync(force=True)
    assert received == [b"old!", b"new!"]


def test_byte_and_file_batch_bounds_allow_one_oversized_file(tmp_path):
    pairs = sources(tmp_path)
    Path(pairs[1][0]).write_bytes(b"x" * 12)
    calls = []
    manager = FileSyncManager(lambda: pairs, lambda *args: pytest.fail("bulk required"), lambda paths: None,
                              bulk_upload_fn=lambda files: calls.append([Path(p).read_bytes() for p, _ in files]),
                              upload_batch_max_files=2, upload_batch_max_bytes=8)
    manager.sync(force=True)
    assert calls == [[b"old!"], [b"x" * 12], [b"old!", b"old!"]]


def test_planning_failure_does_not_escape_or_rate_limit_retry(tmp_path):
    pairs = sources(tmp_path, 1)
    listing = MagicMock(side_effect=[OSError("listing unavailable"), pairs])
    upload = MagicMock()
    manager = FileSyncManager(listing, upload, lambda paths: None)
    manager.sync(force=True)
    assert manager._last_sync_time == 0
    assert manager._pushed_hashes == {}
    manager.sync()
    upload.assert_called_once()


@pytest.mark.parametrize("unconfirmed", ["mapped", "mapped_missing", "inferred", "added_after_push"])
def test_sync_back_preserves_unconfirmed_host_files(tmp_path, unconfirmed):
    confirmed = tmp_path / "a.md"
    pending = tmp_path / "b.md"
    confirmed.write_bytes(b"confirmed local")
    pending.write_bytes(b"newer local")
    pairs = [(str(confirmed), "/remote/a.md")]
    if unconfirmed in {"mapped", "mapped_missing"}:
        pairs.append((str(pending), "/remote/b.md"))

    def upload(files):
        if files[0][1] == "/remote/b.md":
            raise RuntimeError("failed before writing B")

    def download(destination):
        with tarfile.open(destination, "w") as archive:
            for name, content in {"a.md": b"confirmed remote edit", "b.md": b"stale remote",
                                  "new.md": b"remote created"}.items():
                member = tarfile.TarInfo("remote/" + name)
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))

    manager = FileSyncManager(lambda: pairs, lambda *args: None, lambda paths: None,
                              bulk_upload_fn=upload, upload_batch_max_files=1,
                              bulk_download_fn=download)
    manager.sync(force=True)
    assert set(manager._pushed_hashes) == {"/remote/a.md"}
    if unconfirmed == "mapped_missing":
        pending.unlink()
    elif unconfirmed == "added_after_push":
        pairs.append((str(pending), "/remote/b.md"))
    manager.sync_back()
    assert confirmed.read_bytes() == b"confirmed remote edit"
    assert (tmp_path / "new.md").read_bytes() == b"remote created"
    if unconfirmed == "mapped_missing":
        assert not pending.exists()
    else:
        assert pending.read_bytes() == b"newer local"


def test_default_bulk_backend_keeps_single_call(tmp_path):
    pairs = sources(tmp_path)
    upload = MagicMock()
    manager = FileSyncManager(lambda: pairs, lambda *args: pytest.fail("bulk required"), lambda paths: None,
                              bulk_upload_fn=upload)
    manager.sync(force=True)
    upload.assert_called_once()
    assert [remote for _, remote in upload.call_args.args[0]] == [remote for _, remote in pairs]
