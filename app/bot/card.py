from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.audio.models import FIELD_LABELS
from app.bot.keyboards import card_kb


def field_view(data: dict, key: str) -> tuple[str, bool]:
    items = data["items"]
    edits = data["edits"]
    values = [edits[key] if key in edits else item["draft"][key] for item in items]
    changed = any(value != item["original"][key] for value, item in zip(values, items))
    if len(set(values)) > 1:
        return "разные", changed
    return values[0] or "—", changed


def card_text(data: dict) -> str:
    items = data["items"]
    if len(items) == 1:
        lines = [f"🎵 {items[0]['name']}", ""]
    else:
        lines = [f"📚 Файлов: {len(items)}", ""]

    for key, label in FIELD_LABELS.items():
        text, changed = field_view(data, key)
        lines.append(f"{label}: {text}{' ✱' if changed else ''}")

    if data["cover"] == "keep":
        if data["covers"] == len(items):
            status = "есть"
        elif data["covers"]:
            status = "у части файлов"
        else:
            status = "нет"
    elif data["cover"] == "new":
        status = "новая ✱"
    else:
        status = "удалена ✱"
    lines.append(f"Обложка: {status}")

    if len(items) > 1:
        lines += ["", "Правки применятся ко всем файлам"]
    return "\n".join(lines)


async def refresh_card(bot: Bot, chat_id: int, data: dict) -> None:
    with suppress(TelegramBadRequest):
        await bot.edit_message_text(
            card_text(data),
            chat_id=chat_id,
            message_id=data["card_id"],
            reply_markup=card_kb(),
        )
