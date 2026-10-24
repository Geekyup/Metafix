import asyncio
import logging
import re
import shutil
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from app.audio.models import Cover, Tags
from app.audio.registry import get_handler
from app.bot.states import Editing

logger = logging.getLogger(__name__)

router = Router()

AUDIO_SUFFIXES = {".mp3", ".m4a"}


def build_name(tags: Tags, suffix: str, fallback: str) -> str:
    if tags.artist and tags.title:
        base = f"{tags.artist} - {tags.title}"
    elif tags.title:
        base = tags.title
    else:
        return fallback
    base = re.sub(r'[\\/:*?"<>|]', "", base).strip()
    return f"{base}{suffix}" if base else fallback


@router.callback_query(Editing.card, F.data == "done")
async def done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    folder = Path(data["folder"])
    path = folder / data["file"]

    if not path.exists():
        await state.clear()
        await call.message.edit_text("Сессия устарела. Пришли файл заново")
        await call.answer()
        return

    handler = get_handler(path)

    try:
        current = await asyncio.to_thread(handler.read, path)
        tags = Tags(**data["draft"], cover=current.cover)

        if data["cover"] == "removed":
            tags.cover = None
        elif data["cover"] == "new":
            tags.cover = Cover(
                data=(folder / "cover").read_bytes(),
                mime=data["cover_mime"],
            )

        await asyncio.to_thread(handler.write, path, tags)
    except Exception:
        logger.exception("failed to write %s", data["name"])
        await call.answer("Не удалось сохранить файл", show_alert=True)
        return

    filename = build_name(tags, path.suffix, data["name"])
    file = FSInputFile(path, filename=filename)

    if path.suffix.lower() in AUDIO_SUFFIXES:
        await call.message.answer_audio(
            file,
            title=tags.title,
            performer=tags.artist,
        )
    else:
        await call.message.answer_document(file)

    await call.message.edit_text("✅ Готово")
    await call.message.answer("🔁 Пришли следующий аудиофайл: mp3, flac, m4a, ogg или opus")

    shutil.rmtree(folder, ignore_errors=True)
    await state.clear()
    await call.answer()