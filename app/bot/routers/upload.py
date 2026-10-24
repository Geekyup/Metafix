import asyncio
import shutil
import uuid
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.audio.models import FIELD_LABELS
from app.audio.registry import get_handler
from app.bot.card import card_text
from app.bot.keyboards import card_kb
from app.bot.states import Editing
from app.config import settings

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Пришли аудиофайл: mp3, flac, m4a, ogg или opus")


@router.message(F.audio | F.document)
async def on_file(message: Message, bot: Bot, state: FSMContext):
    file = message.audio or message.document
    name = file.file_name or "audio.mp3"

    if file.file_size and file.file_size > settings.max_file_size:
        await message.answer("Файл больше 20 МБ")
        return

    try:
        handler = get_handler(Path(name))
    except ValueError:
        await message.answer("Формат не поддерживается")
        return

    old = await state.get_data()
    if old.get("folder"):
        shutil.rmtree(old["folder"], ignore_errors=True)

    folder = settings.temp_dir / str(message.from_user.id) / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)
    file_on_disk = f"audio{Path(name).suffix.lower()}"
    path = folder / file_on_disk

    await bot.download(file, destination=path)
    tags = await asyncio.to_thread(handler.read, path)

    fields = {key: getattr(tags, key) for key in FIELD_LABELS}
    data = {
        "folder": str(folder),
        "file": file_on_disk,
        "name": name,
        "original": fields,
        "draft": dict(fields),
        "cover": "keep",
        "had_cover": tags.cover is not None,
    }

    card = await message.answer(card_text(data), reply_markup=card_kb())
    data["card_id"] = card.message_id
    await state.set_data(data)
    await state.set_state(Editing.card)