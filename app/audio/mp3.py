from pathlib import Path

from mutagen.id3 import (
    APIC,  # cover image
    ID3,  # reads/writes the tag block of an mp3
    TALB,  # album
    TCON,  # genre
    TDRC,  # year
    TIT2,  # title
    TPE1,  # artist
    TPE2,  # album artist
    TRCK,  # track number
    ID3NoHeaderError,  # raised when the file has no tags yet
)

from app.audio.models import Cover, Tags


def _get(id3: ID3, key: str) -> str | None:
    if key in id3:
        return str(id3[key])
    return None


def _set(id3: ID3, key: str, frame_class, value: str | None) -> None:
    id3.delall(key)
    if value:
        id3.add(frame_class(encoding=3, text=value))


class Mp3Handler:
    def read(self, path: Path) -> Tags:
        try:
            id3 = ID3(path)
        except ID3NoHeaderError:
            return Tags()

        cover = None
        pictures = id3.getall("APIC")
        if pictures:
            cover = Cover(data=pictures[0].data, mime=pictures[0].mime)

        return Tags(
            title=_get(id3, "TIT2"),
            artist=_get(id3, "TPE1"),
            album=_get(id3, "TALB"),
            album_artist=_get(id3, "TPE2"),
            year=_get(id3, "TDRC"),
            track=_get(id3, "TRCK"),
            genre=_get(id3, "TCON"),
            cover=cover,
        )

    def write(self, path: Path, tags: Tags) -> None:
        try:
            id3 = ID3(path)
        except ID3NoHeaderError:
            id3 = ID3()

        _set(id3, "TIT2", TIT2, tags.title)
        _set(id3, "TPE1", TPE1, tags.artist)
        _set(id3, "TALB", TALB, tags.album)
        _set(id3, "TPE2", TPE2, tags.album_artist)
        _set(id3, "TDRC", TDRC, tags.year)
        _set(id3, "TRCK", TRCK, tags.track)
        _set(id3, "TCON", TCON, tags.genre)

        id3.delall("APIC")
        if tags.cover:
            id3.add(
                APIC(
                    encoding=3,
                    mime=tags.cover.mime,
                    type=3,
                    desc="Cover",
                    data=tags.cover.data,
                )
            )

        id3.save(path, v2_version=3)