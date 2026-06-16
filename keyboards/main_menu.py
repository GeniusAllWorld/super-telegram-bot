from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем только нужные функции-генераторы
from keyboards.level1_menu import get_level1_keyboard
from keyboards.level2_menu import get_level2_keyboard
from keyboards.level3_menu import get_level3_keyboard
from keyboards.level4_menu import get_level4_keyboard
from keyboards.level5_menu import get_level5_keyboard

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
    elif level_num == 2:
        kb = get_level2_keyboard()
    elif level_num == 3:
        kb = get_level3_keyboard()
    elif level_num == 4:
        kb = get_level4_keyboard()
    elif level_num == 5:
        kb = get_level5_keyboard()
    else:
        # Заглушка для пока не созданных уровней
        await callback.answer("Уровень еще в разработке!")
        return

    await callback.message.edit_text(
        text=f"Вы выбрали Уровень {level_num}. Что делаем?",
        reply_markup=kb
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        text="🤖 Главное меню GeniusBot.\nВыберите уровень разработки:",
        reply_markup=get_main_menu()
    )
    await callback.answer()