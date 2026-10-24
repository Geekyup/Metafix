from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.audio.models import FIELD_LABELS


def card_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, label in FIELD_LABELS.items():
        kb.button(text=f"✏️ {label}", callback_data=f"f:{key}")
    kb.button(text="🖼 Обложка", callback_data="cover")
    kb.button(text="↩️ Сбросить", callback_data="reset")
    kb.button(text="🧹 Очистить всё", callback_data="clear")
    kb.button(text="✅ Готово", callback_data="done")
    kb.adjust(2, 2, 2, 1, 1, 2, 1)
    return kb.as_markup()


def value_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🧽 Очистить поле", callback_data="clear_field")
    kb.button(text="Отмена", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()


def cover_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Убрать обложку", callback_data="cover_remove")
    kb.button(text="Отмена", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()