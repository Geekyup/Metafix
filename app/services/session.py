import re
from pathlib import Path

TRACK_PREFIX = re.compile(r"^\d{1,3}\s*[.\-)]+\s*")


def parse_name(name: str) -> dict[str, str]:
    stem = TRACK_PREFIX.sub("", Path(name).stem).replace("_", " ").strip()
    artist, sep, title = stem.partition(" - ")
    artist, title = artist.strip(), title.strip()
    if not sep or not artist or not title:
        return {}
    return {"artist": artist, "title": title}