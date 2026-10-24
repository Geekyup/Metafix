from pathlib import Path
from typing import Protocol

from app.audio.models import Tags


class AudioHandler(Protocol):
    def read(self, path: Path) -> Tags: 
        pass

    def write(self, path: Path, tags: Tags) -> None: 
        pass