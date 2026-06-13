from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем только нужные функции-генераторы
from keyboards.level1_menu import get_level1_keyboard

router = Router()

def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=f"Уровень {i}", callback_data=f"level_{i}"))
    builder.adjust(2)
    return builder.as_markup()

# Обработчик здесь же
@router.callback_query(F.data.startswith("level_"))
async def level_selection_handler(callback: CallbackQuery):
    level_num = int(callback.data.split("_")[1])
    
    # Динамический выбор клавиатуры
    if level_num == 1:
        kb = get_level1_keyboard()
    else:
        # Заглушка для пока не созданных уровней
        await callback.answer("Уровень еще в разработке!")
        return

    await callback.message.edit_text(
        text=f"Вы выбрали Уровень {level_num}. Что делаем?",
        reply_markup=kb
    )