"""Cross-process activity leases for an externally managed CDP browser.

A user-supplied launcher can watch ``browser.cdp_activity_dir`` and stop its
browser only after ``last_used`` is old and ``leases/`` is empty.  Hermes owns
only the lease files; browser process policy stays with the launcher.
"""

from __future__ import annotations

import contextlib
import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

_HEARTBEAT_SECONDS = 30.0


def _activity_root() -> Optional[Path]:
    """Return the configured activity directory only for an explicit CDP route."""
    try:
        from hermes_cli.config import cfg_get, read_raw_config

        cfg = cfg_get(read_raw_config(), "browser", default={})
    except Exception:
        return None
    if not isinstance(cfg, dict):
        return None
    endpoint = (
        os.environ.get("BROWSER_CDP_URL", "").strip()
        or str(cfg.get("cdp_url") or "").strip()
        or str(cfg.get("cdp_endpoint") or "").strip()
    )
    raw_dir = str(cfg.get("cdp_activity_dir") or "").strip()
    if not endpoint or not raw_dir:
        return None
    return Path(raw_dir).expanduser()


@contextmanager
def _state_lock(root: Path) -> Iterator[None]:
    """Serialize lease transitions with an external watchdog on Windows or POSIX."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / "state.lock"
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


def _heartbeat(lease: Path, stop: threading.Event) -> None:
    while not stop.wait(_HEARTBEAT_SECONDS):
        with contextlib.suppress(OSError):
            lease.touch(exist_ok=True)


@contextmanager
def activity_lease() -> Iterator[None]:
    """Publish one live browser operation and always release it on return/error."""
    root = _activity_root()
    if root is None:
        yield
        return

    leases = root / "leases"
    lease = leases / f"{os.getpid()}-{threading.get_ident()}-{uuid.uuid4().hex}.lease"
    with _state_lock(root):
        leases.mkdir(parents=True, exist_ok=True)
        lease.write_text(
            json.dumps({"pid": os.getpid(), "started_at": time.time()}),
            encoding="utf-8",
        )
        _touch(root / "last_used")

    stop = threading.Event()
    heartbeat: Optional[threading.Thread] = None
    try:
        from agent.memory_provider import spawn_context_thread

        heartbeat = spawn_context_thread(
            _heartbeat,
            name="browser-cdp-activity",
            args=(lease, stop),
        )
        heartbeat.start()
        yield
    finally:
        stop.set()
        if heartbeat is not None and heartbeat.is_alive():
            heartbeat.join(timeout=1.0)
        with _state_lock(root):
            lease.unlink(missing_ok=True)
            _touch(root / "last_used")
