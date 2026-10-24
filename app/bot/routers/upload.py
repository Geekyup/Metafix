import asyncio
import logging
import shutil
import uuid
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.audio.models import FIELD_LABELS
from app.audio.registry import SUFFIXES, detect, extension, get_handler
from app.bot.card import card_text
from app.bot.keyboards import card_kb
from app.bot.states import Editing
from app.config import settings
from app.services.session import parse_name

logger = logging.getLogger(__name__)

router = Router()

albums: dict[str, list[Message]] = {}


def file_name(message: Message) -> str:
    file = message.audio or message.document
    return file.file_name or "audio.mp3"


async def load_item(bot: Bot, message: Message, folder: Path, index: int) -> dict:
    file = message.audio or message.document
    name = file_name(message)

    if file.file_size and file.file_size > settings.max_file_size:
        raise ValueError("файл слишком большой")

    mime = file.mime_type or ""
    if not (mime.startswith("audio/") or Path(name).suffix.lower() in SUFFIXES):
        raise ValueError("формат не поддерживается")

    tmp = folder / f"{index:02d}.tmp"
    await bot.download(file, destination=tmp)

    kind = detect(tmp)
    if kind is None:
        raise ValueError("формат не поддерживается")

    path = tmp.with_suffix(extension(kind, Path(name).suffix))
    tmp.rename(path)

    tags = await asyncio.to_thread(get_handler(path).read, path)
    original = {key: getattr(tags, key) for key in FIELD_LABELS}
    draft = dict(original)
    for key, value in parse_name(name).items():
        if not draft[key]:
            draft[key] = value

    return {
        "file": path.name,
        "name": name,
        "original": original,
        "draft": draft,
        "cover": tags.cover is not None,
    }


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Пришли один или несколько аудиофайлов: mp3, flac, m4a, ogg или opus")


@router.message(F.audio | F.document)
async def on_file(message: Message, bot: Bot, state: FSMContext):
    group = message.media_group_id
    if group:
        bucket = albums.setdefault(group, [])
        bucket.append(message)
        if len(bucket) > 1:
            return
        await asyncio.sleep(1)
        messages = sorted(albums.pop(group), key=lambda m: m.message_id)
    else:
        messages = [message]

    folder = settings.temp_dir / str(message.from_user.id) / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)

    items = []
    skipped = []
    for index, msg in enumerate(messages):
        try:
            items.append(await load_item(bot, msg, folder, index))
        except ValueError as e:
            skipped.append(f"{file_name(msg)}: {e}")
        except Exception:
            logger.exception("failed to read %s", file_name(msg))
            skipped.append(f"{file_name(msg)}: не удалось прочитать")

    if not items:
        shutil.rmtree(folder, ignore_errors=True)
        await message.answer("Не удалось обработать файлы:\n" + "\n".join(skipped))
        return

    old = await state.get_data()
    if old.get("folder"):
        shutil.rmtree(old["folder"], ignore_errors=True)

    data = {
        "folder": str(folder),
        "items": items,
        "edits": {},
        "cover": "keep",
        "covers": sum(1 for item in items if item["cover"]),
    }

    card = await message.answer(card_text(data), reply_markup=card_kb())
    data["card_id"] = card.message_id
    await state.set_data(data)
    await state.set_state(Editing.card)

    if skipped:
        await message.answer("Пропущено:\n" + "\n".join(skipped))
