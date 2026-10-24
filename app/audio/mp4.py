from pathlib import Path

from mutagen.mp4 import MP4, MP4Cover

from app.audio.models import Cover, Tags

TEXT_KEYS = {
    "title": "\xa9nam",
    "artist": "\xa9ART",
    "album": "\xa9alb",
    "album_artist": "aART",
    "year": "\xa9day",
    "genre": "\xa9gen",
}


class Mp4Handler:
    def read(self, path: Path) -> Tags:
        audio = MP4(path)
        tags = audio.tags or {}

        values = {}
        for name, key in TEXT_KEYS.items():
            items = tags.get(key)
            values[name] = items[0] if items else None

        track = None
        trkn = tags.get("trkn")
        if trkn:
            number, total = trkn[0]
            if number:
                track = f"{number}/{total}" if total else str(number)

        cover = None
        covr = tags.get("covr")
        if covr:
            image = covr[0]
            mime = "image/png" if image.imageformat == MP4Cover.FORMAT_PNG else "image/jpeg"
            cover = Cover(data=bytes(image), mime=mime)

        return Tags(**values, track=track, cover=cover)

    def write(self, path: Path, tags: Tags) -> None:
        audio = MP4(path)
        if audio.tags is None:
            audio.add_tags()

        for name, key in TEXT_KEYS.items():
            value = getattr(tags, name)
            if value:
                audio[key] = [value]
            elif key in audio:
                del audio[key]

        if tags.track:
            head, _, tail = tags.track.partition("/")
            audio["trkn"] = [(int(head), int(tail) if tail else 0)]
        elif "trkn" in audio:
            del audio["trkn"]

        if tags.cover:
            fmt = MP4Cover.FORMAT_PNG if tags.cover.mime == "image/png" else MP4Cover.FORMAT_JPEG
            audio["covr"] = [MP4Cover(tags.cover.data, imageformat=fmt)]
        elif "covr" in audio:
            del audio["covr"]

        audio.save()