from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.audio.models import FIELD_LABELS
from app.bot.keyboards import card_kb


def card_text(data: dict) -> str:
    lines = [f"🎵 {data['name']}", ""]
    for key, label in FIELD_LABELS.items():
        value = data["draft"][key]
        mark = " ✱" if value != data["original"][key] else ""
        lines.append(f"{label}: {value or '—'}{mark}")

    if data["cover"] == "keep":
        status = "есть" if data["had_cover"] else "нет"
    elif data["cover"] == "new":
        status = "новая ✱"
    else:
        status = "удалена ✱"
    lines.append(f"Обложка: {status}")
    return "\n".join(lines)


async def refresh_card(bot: Bot, chat_id: int, data: dict) -> None:
    with suppress(TelegramBadRequest):
        await bot.edit_message_text(
            card_text(data),
            chat_id=chat_id,
            message_id=data["card_id"],
            reply_markup=card_kb(),
        )