from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.audio.models import FIELD_LABELS
from app.bot.card import refresh_card
from app.bot.keyboards import value_kb
from app.bot.states import Editing

router = Router()


def check(field: str, value: str) -> None:
    if len(value) > 256:
        raise ValueError("Слишком длинное значение")
    if field == "year" and not (value.isdigit() and len(value) == 4):
        raise ValueError("Год: 4 цифры, например 2003")
    if field == "track":
        head, _, tail = value.partition("/")
        if not head.isdigit() or (tail and not tail.isdigit()):
            raise ValueError("Трек: число или 3/12")


async def apply_value(state: FSMContext, bot: Bot, chat_id: int, value: str | None):
    data = await state.get_data()
    draft = {**data["draft"], data["field"]: value}
    await state.update_data(draft=draft)
    await state.set_state(Editing.card)
    await refresh_card(bot, chat_id, await state.get_data())


@router.callback_query(Editing.card, F.data.startswith("f:"))
async def pick_field(call: CallbackQuery, state: FSMContext):
    field = call.data.split(":", 1)[1]
    data = await state.get_data()
    current = data["draft"][field] or "—"
    await state.update_data(field=field)
    await state.set_state(Editing.value)
    await call.message.edit_text(
        f"{FIELD_LABELS[field]}\nСейчас: {current}\n\nПришли новое значение",
        reply_markup=value_kb(),
    )
    await call.answer()


@router.message(Editing.value, F.text)
async def set_value(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    value = message.text.strip()

    with suppress(TelegramBadRequest):
        await message.delete()

    if not value or value == "-":
        await apply_value(state, bot, message.chat.id, None)
        return

    try:
        check(data["field"], value)
    except ValueError as e:
        with suppress(TelegramBadRequest):
            await bot.edit_message_text(
                f"{e}\n\nПопробуй ещё раз",
                chat_id=message.chat.id,
                message_id=data["card_id"],
                reply_markup=value_kb(),
            )
        return

    await apply_value(state, bot, message.chat.id, value)


@router.callback_query(Editing.value, F.data == "clear_field")
async def clear_field(call: CallbackQuery, state: FSMContext, bot: Bot):
    await apply_value(state, bot, call.message.chat.id, None)
    await call.answer("Поле очищено")


@router.callback_query(StateFilter(Editing.value, Editing.cover), F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(Editing.card)
    await refresh_card(bot, call.message.chat.id, await state.get_data())
    await call.answer()


@router.callback_query(Editing.card, F.data == "reset")
async def reset(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data(draft=dict(data["original"]), cover="keep")
    await refresh_card(bot, call.message.chat.id, await state.get_data())
    await call.answer("Сброшено")


@router.callback_query(Editing.card, F.data == "clear")
async def clear_all(call: CallbackQuery, state: FSMContext, bot: Bot):
    draft = {key: None for key in FIELD_LABELS}
    await state.update_data(draft=draft, cover="removed")
    await refresh_card(bot, call.message.chat.id, await state.get_data())
    await call.answer("Всё очищено")