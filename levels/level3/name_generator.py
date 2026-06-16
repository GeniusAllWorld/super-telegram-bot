import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest # Импортируем для отлова специфических ошибок API

router = Router()

# Слоги для генерации имён по расам
NAME_COMPONENTS = {
    "elf": {
        "prefixes": ["Эл", "Ле", "Тал", "Ил", "Фин", "Глор", "Ара", "Гала"],
        "roots": ["онд", "дари", "риан", "анор", "лад", "фил", "мил", "вен"],
        "suffixes": ["ас", "ис", "иль", "ион", "ель", "дуил", "дор", "эль"]
    },
    "dwarf": {
        "prefixes": ["Тор", "Ба", "Два", "Гло", "Фли", "Ду", "Бра", "Тра"],
        "roots": ["ин", "ли", "вали", "рум", "грим", "инд", "ок", "гар"],
        "suffixes": ["льд", "р", "н", "рдин", "кли", "ор", "бек", "даг"]
    },
    "orc": {
        "prefixes": ["Гар", "Гrom", "Азг", "Угр", "Трак", "Дуг", "Шаг", "Болг"],
        "roots": ["маш", "гар", "дук", "рог", "нак", "гул", "зог", "тар"],
        "suffixes": ["ил", "аг", "ук", "ар", "рон", "бат", "орк", "гаш"]
    }
}


# Функция сборки инлайн-клавиатуры выбора расы
def get_race_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🧝‍♂️ Эльф", callback_data="gen_name:elf"),
        InlineKeyboardButton(text="🧔 Гном", callback_data="gen_name:dwarf"),
        InlineKeyboardButton(text="👹 Орк", callback_data="gen_name:orc")
    )
    return builder.as_markup()


# Хэндлер инициализации генератора имён
@router.callback_query(F.data == "cmd_name_gen")
async def start_name_generator(callback: CallbackQuery):
    await callback.message.answer(
        "🔮 <b>Генератор фэнтези-имен</b>\n\n"
        "Выберите расу вашего будущего персонажа:",
        reply_markup=get_race_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# Хэндлер обработки клика по расе, рандомизации слогов и обновления интерфейса
@router.callback_query(F.data.startswith("gen_name:"))
async def process_name_generation(callback: CallbackQuery):
    race = callback.data.split(":")[1]
    
    components = NAME_COMPONENTS.get(race)
    if not components:
        await callback.message.answer("❌ Произошла ошибка. Раса не найдена.")
        await callback.answer()
        return
        
    # Генерируем имя, склеивая случайные части префикса, корня и суффикса
    prefix = random.choice(components["prefixes"])
    root = random.choice(components["roots"])
    suffix = random.choice(components["suffixes"])
    
    generated_name = f"{prefix}{root}{suffix}".capitalize()
    
    race_titles = {
        "elf": "🧝‍♂️ Эльфийское имя",
        "dwarf": "🧔 Гномье имя",
        "orc": "👹 Орочье имя"
    }
    
    try:
        # Меняем текст сообщения на результат, сохраняя кнопки для повторной генерации
        await callback.message.edit_text(
            f"{race_titles[race]}:\n"
            f"✨ <b>{generated_name}</b> ✨\n\n"
            f"Не понравилось? Можешь сгенерировать заново:",
            reply_markup=get_race_keyboard(),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        # Пофиксили баг: если рандом выдал абсолютно то же самое имя, гасим ошибку "message is not modified"
        if "message is not modified" in str(e):
            # Можно сделать всплывающее уведомление, что имя совпало, чтобы юзер понимал, что клик прошел
            await callback.answer("🎲 Выпало то же самое имя! Нажми еще раз.")
            return
        # Если прилетела какая-то другая ошибка редактирования — пробрасываем её дальше
        raise e
        
    # Закрываем часики на кнопке в любом случае
    await callback.answer()