from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.level1_menu import get_level1_keyboard
from keyboards.level2_menu import get_level2_keyboard
from keyboards.level3_menu import get_level3_keyboard
from keyboards.level4_menu import get_level4_keyboard
from keyboards.level5_menu import get_level5_keyboard

router = Router()

# Карта соответствия номеров уровней и их функций-генераторов клавиатур
# Помогает избежать громоздких конструкций if/elif
LEVEL_KEYBOARDS = {
    1: get_level1_keyboard,
    2: get_level2_keyboard,
    3: get_level3_keyboard,
    4: get_level4_keyboard,
    5: get_level5_keyboard
}


def get_main_menu() -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру главного меню бота.
    Создает сетку кнопок для выбора доступных уровней (с 1 по 5)
    и выстраивает их по 2 штуки в ряд.
    """
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=f"Уровень {i}", callback_data=f"level_{i}"))
    builder.adjust(2)
    return builder.as_markup()


@router.callback_query(F.data.startswith("level_"))
async def level_selection_handler(callback: CallbackQuery):
    """
    Обрабатывает нажатие на кнопку выбора уровня.
    Динамически извлекает функцию генерации клавиатуры из словаря LEVEL_KEYBOARDS,
    изменяет текст сообщения и обновляет клавиатуру на выбранный уровень.
    """
    level_num = int(callback.data.split("_")[1])
    
    # Получаем нужную функцию из словаря. Если уровня нет — вернет None
    keyboard_getter = LEVEL_KEYBOARDS.get(level_num)
    
    if not keyboard_getter:
        await callback.answer("Уровень еще в разработке!", show_alert=True)
        return

    # Вызываем функцию и получаем клавиатуру
    kb = keyboard_getter()

    await callback.message.edit_text(
        text=f"Вы выбрали Уровень {level_num}. Что делаем?",
        reply_markup=kb
    )
    await callback.answer()  # Убирает бесконечную загрузку (часики) на кнопке


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Обрабатывает нажатие кнопки возврата в главное меню.
    Сбрасывает текущий интерфейс уровня, возвращая пользователю
    стартовое меню выбора уровней.
    """
    await callback.message.edit_text(
        text="🤖 Главное меню GeniusBot.\nВыберите уровень разработки:",
        reply_markup=get_main_menu()
    )
    await callback.answer()