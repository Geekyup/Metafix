import base64
from pathlib import Path

from mutagen import MutagenError
from mutagen.flac import FLAC, Picture
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from app.audio.models import Cover, Tags

KEYS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "albumartist",
    "year": "date",
    "track": "tracknumber",
    "genre": "genre",
}


def _make_picture(cover: Cover) -> Picture:
    pic = Picture()
    pic.type = 3
    pic.mime = cover.mime
    pic.data = cover.data
    return pic


class VorbisHandler:
    def load(self, path: Path):
        raise NotImplementedError

    def read_cover(self, audio) -> Cover | None:
        raise NotImplementedError

    def write_cover(self, audio, cover: Cover | None) -> None:
        raise NotImplementedError

    def read(self, path: Path) -> Tags:
        audio = self.load(path)
        values = {}
        for name, key in KEYS.items():
            items = audio.get(key)
            values[name] = items[0] if items else None
        return Tags(**values, cover=self.read_cover(audio))

    def write(self, path: Path, tags: Tags) -> None:
        audio = self.load(path)
        for name, key in KEYS.items():
            value = getattr(tags, name)
            if value:
                audio[key] = [value]
            elif key in audio:
                del audio[key]
        self.write_cover(audio, tags.cover)
        audio.save()


class FlacHandler(VorbisHandler):
    def load(self, path: Path):
        return FLAC(path)

    def read_cover(self, audio) -> Cover | None:
        if audio.pictures:
            pic = audio.pictures[0]
            return Cover(data=pic.data, mime=pic.mime)
        return None

    def write_cover(self, audio, cover: Cover | None) -> None:
        audio.clear_pictures()
        if cover:
            audio.add_picture(_make_picture(cover))


class OggHandler(VorbisHandler):
    def load(self, path: Path):
        try:
            return OggVorbis(path)
        except MutagenError:
            return OggOpus(path)

    def read_cover(self, audio) -> Cover | None:
        for raw in audio.get("metadata_block_picture", []):
            pic = Picture(base64.b64decode(raw))
            return Cover(data=pic.data, mime=pic.mime)
        return None

    def write_cover(self, audio, cover: Cover | None) -> None:
        if "metadata_block_picture" in audio:
            del audio["metadata_block_picture"]
        if cover:
            encoded = base64.b64encode(_make_picture(cover).write()).decode("ascii")
            audio["metadata_block_picture"] = [encoded]