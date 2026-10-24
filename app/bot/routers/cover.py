from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.card import refresh_card
from app.bot.keyboards import cover_kb
from app.bot.states import Editing

router = Router()

IMAGE_MIMES = {"image/jpeg", "image/png"}


@router.callback_query(Editing.card, F.data == "cover")
async def ask_cover(call: CallbackQuery, state: FSMContext):
    await state.set_state(Editing.cover)
    await call.message.edit_text("Пришли картинку для обложки", reply_markup=cover_kb())
    await call.answer()


@router.callback_query(Editing.cover, F.data == "cover_remove")
async def remove_cover(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(cover="removed")
    await state.set_state(Editing.card)
    await refresh_card(bot, call.message.chat.id, await state.get_data())
    await call.answer()


@router.message(
    Editing.cover,
    F.photo | (F.document & F.document.mime_type.in_(IMAGE_MIMES)),
)
async def set_cover(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    if message.photo:
        file = message.photo[-1]
        mime = "image/jpeg"
    else:
        file = message.document
        mime = file.mime_type

    await bot.download(file, destination=Path(data["folder"]) / "cover")
    await state.update_data(cover="new", cover_mime=mime)
    await state.set_state(Editing.card)
    await message.delete()
    await refresh_card(bot, message.chat.id, await state.get_data())