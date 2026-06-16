from aiogram.fsm.state import State, StatesGroup

# Состояния для функций Первого Уровня (Базовые команды)
class Level1States(StatesGroup):
    waiting_for_photo = State()  # Ожидание фотографии для получения информации об аватаре

# Состояния для функций Второго Уровня (Полезные утилиты)
class Level2States(StatesGroup):
    waiting_for_random_max = State()       # Ожидание верхней границы для рандомайзера
    waiting_for_weather_city = State()     # Ожидание названия города для прогноза погоды
    waiting_for_qr_text = State()          # Ожидание текста или ссылки для генерации QR-кода
    waiting_for_url = State()              # Ожидание длинной ссылки для сокращателя
    waiting_for_timer_time = State()       # Ожидание количества минут для таймера
    waiting_for_alarm_date = State()       # Ожидание даты для установки будильника
    waiting_for_alarm_time = State()       # Ожидание времени для установки будильника
    waiting_for_translate_text = State()   # Ожидание текста для переводчика
    waiting_for_calc_expression = State()  # Ожидание математического выражения для калькулятора

# Состояния для функций Третьего Уровня (Медиа и развлечения)
class Level3States(StatesGroup):
    waiting_for_gif_query = State()        # Ожидание поискового запроса для GIF
    waiting_for_quiz_answer = State()      # Ожидание ответа пользователя на викторину
    waiting_for_meme_photo = State()       # Ожидание картинки-шаблона для генератора мемов
    waiting_for_meme_text = State()        # Ожидание текста, который наложится на мем
    waiting_for_text_to_analyze = State()  # Ожидание текста для лингвистического анализа
    waiting_for_wiki_query = State()       # Ожидание поискового запроса для Википедии
    waiting_for_video = State()            # Ожидание видеофайла для конвертации в аудио
    waiting_for_sticker = State()          # Ожидание стикера для вывода технической инфы

# Состояния для функций Четвертого Уровня (Инструменты разработчика и админа)
class Level4States(StatesGroup):
    waiting_for_sql = State()         # Ожидание сырого SQL-запроса для админской консоли
    waiting_for_eval = State()        # Ожидание Python-кода для динамического выполнения
    ai_chat = State()                 # Состояние активного диалога с ИИ-автоответчиком
    waiting_for_voice = State()       # Ожидание голосового сообщения для Whisper STT
    waiting_for_photo = State()       # Ожидание изображения для распознавания текста (OCR)
    waiting_for_wl_add = State()      # Ожидание Telegram ID для добавления в белый список
    waiting_for_wl_remove = State()   # Ожидание Telegram ID для удаления из белого списка