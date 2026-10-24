from pathlib import Path

from app.audio.mp3 import Mp3Handler
from app.audio.mp4 import Mp4Handler
from app.audio.vorbis import FlacHandler, OggHandler

SUFFIXES = {".mp3", ".flac", ".m4a", ".ogg", ".opus"}

HANDLERS = {
    "mp3": Mp3Handler(),
    "flac": FlacHandler(),
    "m4a": Mp4Handler(),
    "ogg": OggHandler(),
}

EXTENSIONS = {
    "mp3": ".mp3",
    "flac": ".flac",
    "m4a": ".m4a",
    "ogg": ".ogg",
}


def detect(path: Path) -> str | None:
    with path.open("rb") as f:
        head = f.read(12)
    if head[:3] == b"ID3":
        return "mp3"
    if len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0 and head[1] & 0x06:
        return "mp3"
    if head[:4] == b"fLaC":
        return "flac"
    if head[:4] == b"OggS":
        return "ogg"
    if head[4:8] == b"ftyp":
        return "m4a"
    return None


def extension(kind: str, original: str) -> str:
    if kind == "ogg" and original.lower() == ".opus":
        return ".opus"
    return EXTENSIONS[kind]


def get_handler(path: Path):
    kind = detect(path)
    if kind is None:
        raise ValueError("Unsupported format")
    return HANDLERS[kind]
