import asyncio
import logging
import shutil
import time
from contextlib import suppress
from pathlib import Path

logger = logging.getLogger(__name__)


def clean_once(root: Path, ttl: int) -> None:
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


async def cleanup_loop(root: Path, ttl: int, interval: int = 600) -> None:
    while True:
        try:
            await asyncio.to_thread(clean_once, root, ttl)
        except Exception:
            logger.exception("cleanup failed")
        await asyncio.sleep(interval)