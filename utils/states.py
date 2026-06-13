from aiogram.fsm.state import State, StatesGroup

class AvatarStates(StatesGroup):
    waiting_for_photo = State()