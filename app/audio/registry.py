from pathlib import Path

from app.audio.mp3 import Mp3Handler

HANDLERS = {
    ".mp3": Mp3Handler(),
}


def get_handler(path: Path):
    handler = HANDLERS.get(path.suffix.lower())
    if handler is None:
        raise ValueError(f"Unsupported format: {path.suffix}")
    return handler