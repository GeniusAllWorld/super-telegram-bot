import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

router = Router()

# Варианты игры
OPTIONS = ["Камень", "Ножницы", "Бумага"]


# Функция генерации клавиатуры выбора хода
def get_rps_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🪨 Камень", callback_data="rps:Камень"),
        InlineKeyboardButton(text="✂️ Ножницы", callback_data="rps:Ножницы"),
        InlineKeyboardButton(text="📄 Бумага", callback_data="rps:Бумага")
    )
    return builder.as_markup()


# Функция генерации кнопки повторной игры после завершения раунда
def get_replay_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Играть снова", callback_data="cmd_rps_game")
    )
    return builder.as_markup()


# Хэндлер инициализации и вывода стартового меню игры
@router.callback_query(F.data == "cmd_rps_game")
async def start_rps(callback: CallbackQuery):
    # Используем edit_text вместо answer, чтобы игра шла в одном красивом окне при перезапусках
    try:
        await callback.message.edit_text(
            "✊✋✌️ <b>Камень, Ножницы, Бумага!</b>\n\nВыбирай свой вариант:", 
            reply_markup=get_rps_keyboard(), 
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        # Если меню уже открыто и юзер спамит кнопку "Играть снова", просто гасим ошибку
        pass
    await callback.answer()


# Хэндлер обработки хода игрока, генерации ответа бота и сверки результатов
@router.callback_query(F.data.startswith("rps:"))
async def process_rps(callback: CallbackQuery):
    user_choice = callback.data.split(":")[1]
    bot_choice = random.choice(OPTIONS)
    
    # Логика определения победителя игры
    if user_choice == bot_choice:
        result = "🤝 <b>Ничья!</b>"
    elif (user_choice == "Камень" and bot_choice == "Ножницы") or \
         (user_choice == "Ножницы" and bot_choice == "Бумага") or \
         (user_choice == "Бумага" and bot_choice == "Камень"):
        result = "🎉 <b>Ты победил!</b>"
    else:
        result = "🤖 <b>Бот победил!</b>"
        
    try:
        # Обновляем текст сообщения, выводя итог раунда и подкрепляя кнопку перезапуска
        await callback.message.edit_text(
            f"👤 Ты: <b>{user_choice}</b>\n"
            f"🤖 Бот: <b>{bot_choice}</b>\n\n"
            f"{result}\n\n"
            f"Хочешь реванш?",
            reply_markup=get_replay_keyboard(),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        # Пофиксили баг: если выпадает дубликат исхода, сообщаем юзеру через всплывающее окно
        if "message is not modified" in str(e):
            await callback.answer(f"🎲 Снова {user_choice}! Результат не изменился, попробуй еще раз.")
            return
        raise e
        
    # Пофиксили баг: гасим часики анимации на инлайн-кнопке
    await callback.answer()