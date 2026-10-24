from aiogram.fsm.state import State, StatesGroup


class Editing(StatesGroup):
    card = State()
    value = State()
    cover = State()