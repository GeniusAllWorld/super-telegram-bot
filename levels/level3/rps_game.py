import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Варианты игры
OPTIONS = ["Камень", "Ножницы", "Бумага"]

def get_rps_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🪨 Камень", callback_data="rps:Камень"),
        InlineKeyboardButton(text="✂️ Ножницы", callback_data="rps:Ножницы"),
        InlineKeyboardButton(text="📄 Бумага", callback_data="rps:Бумага")
    )
    return builder.as_markup()

@router.callback_query(F.data == "cmd_rps_game")
async def start_rps(callback: CallbackQuery):
    await callback.message.answer("✊✋✌️ <b>Камень, Ножницы, Бумага!</b>\n\nВыбирай свой вариант:", 
                                  reply_markup=get_rps_keyboard(), 
                                  parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("rps:"))
async def process_rps(callback: CallbackQuery):
    user_choice = callback.data.split(":")[1]
    bot_choice = random.choice(OPTIONS)
    
    # Логика определения победителя
    result = ""
    if user_choice == bot_choice:
        result = "🤝 <b>Ничья!</b>"
    elif (user_choice == "Камень" and bot_choice == "Ножницы") or \
         (user_choice == "Ножницы" and bot_choice == "Бумага") or \
         (user_choice == "Бумага" and bot_choice == "Камень"):
        result = "🎉 <b>Ты победил!</b>"
    else:
        result = "🤖 <b>Бот победил!</b>"
        
    await callback.message.edit_text(
        f"👤 Ты: <b>{user_choice}</b>\n"
        f"🤖 Бот: <b>{bot_choice}</b>\n\n"
        f"{result}",
        parse_mode="HTML"
    )