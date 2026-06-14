from aiogram.fsm.state import State, StatesGroup

class AvatarStates(StatesGroup):
    waiting_for_photo = State()

class Level2States(StatesGroup):
    waiting_for_random_max = State()
    waiting_for_weather_city = State()
    waiting_for_qr_text = State()
    waiting_for_url = State()
    waiting_for_timer_time = State()
    waiting_for_alarm_date = State()
    waiting_for_alarm_time = State() 
    waiting_for_translate_text = State()
    waiting_for_calc_expression = State()

class Level3States(StatesGroup):
    waiting_for_gif_query = State()