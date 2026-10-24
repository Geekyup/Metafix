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
        return f"{Path(fallback).stem}{suffix}"
    base = re.sub(r'[\\/:*?"<>|]', "", base).strip()
    return f"{base}{suffix}" if base else f"{Path(fallback).stem}{suffix}"


@router.callback_query(Editing.card, F.data == "done")
async def done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    folder = Path(data["folder"])
    items = data["items"]

    if not all((folder / item["file"]).exists() for item in items):
        await state.clear()
        await call.message.edit_text("Сессия устарела. Пришли файл заново")
        await call.answer()
        return

    results = []
    try:
        new_cover = None
        if data["cover"] == "new":
            new_cover = Cover(
                data=(folder / "cover").read_bytes(),
                mime=data["cover_mime"],
            )

        for item in items:
            path = folder / item["file"]
            handler = get_handler(path)
            current = await asyncio.to_thread(handler.read, path)
            tags = Tags(**{**item["draft"], **data["edits"]}, cover=current.cover)

            if data["cover"] == "removed":
                tags.cover = None
            elif data["cover"] == "new":
                tags.cover = new_cover

            await asyncio.to_thread(handler.write, path, tags)
            results.append((path, tags, item["name"]))
    except Exception:
        logger.exception("failed to write files")
        await call.answer("Не удалось сохранить файлы", show_alert=True)
        return

    names = [build_name(tags, path.suffix, name) for path, tags, name in results]
    if len(set(names)) < len(names):
        names = [f"{Path(name).stem}{path.suffix}" for path, _, name in results]

    for (path, tags, _), filename in zip(results, names):
        file = FSInputFile(path, filename=filename)
        if path.suffix.lower() in AUDIO_SUFFIXES:
            await call.message.answer_audio(file, title=tags.title, performer=tags.artist)
        else:
            await call.message.answer_document(file)
        if len(results) > 1:
            await asyncio.sleep(0.5)

    await call.message.edit_text("✅ Готово")
    await call.message.answer("🔁 Пришли следующий аудиофайл: mp3, flac, m4a, ogg или opus")

    shutil.rmtree(folder, ignore_errors=True)
    await state.clear()
    await call.answer()
