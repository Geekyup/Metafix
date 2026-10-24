from dataclasses import dataclass


@dataclass
class Cover:
    data: bytes
    mime: str = "image/jpeg"


@dataclass
class Tags:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    year: str | None = None
    track: str | None = None
    genre: str | None = None
    cover: Cover | None = None


FIELD_LABELS = {
    "title": "Название",
    "artist": "Исполнитель",
    "album": "Альбом",
    "album_artist": "Исполнитель альбома",
    "year": "Год",
    "track": "Трек",
    "genre": "Жанр",
}