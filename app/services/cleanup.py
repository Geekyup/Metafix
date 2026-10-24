import asyncio
import logging
import shutil
import time
from contextlib import suppress
from pathlib import Path

logger = logging.getLogger(__name__)

API_FILE_DIRS = ("documents", "music", "photos")


def clean_sessions(root: Path, ttl: int) -> None:
    if not root.exists():
        return
    now = time.time()
    for user_dir in root.iterdir():
        if not user_dir.is_dir():
            continue
        for session in user_dir.iterdir():
            if session.is_dir() and now - session.stat().st_mtime > ttl:
                shutil.rmtree(session, ignore_errors=True)
        with suppress(OSError):
            if not any(user_dir.iterdir()):
                user_dir.rmdir()


def clean_api_files(root: Path, ttl: int) -> None:
    if not root.exists():
        return
    now = time.time()
    for folder in API_FILE_DIRS:
        for file in root.glob(f"*/{folder}/*"):
            if file.is_file() and now - file.stat().st_mtime > ttl:
                file.unlink(missing_ok=True)


async def cleanup_loop(
    root: Path,
    ttl: int,
    api_dir: Path | None = None,
    interval: int = 600,
) -> None:
    while True:
        try:
            await asyncio.to_thread(clean_sessions, root, ttl)
            if api_dir:
                await asyncio.to_thread(clean_api_files, api_dir, ttl)
        except Exception:
            logger.exception("cleanup failed")
        await asyncio.sleep(interval)
