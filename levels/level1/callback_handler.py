from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

# Словарь для обработки callback-ов
CALLBACK_ACTIONS = {
    "cmd_start": "/start",
    "cmd_help": "/help",
    "cmd_echo": "Просто напиши что-нибудь в чат!",
    "cmd_ping": "/ping",
    "cmd_userinfo": "/userinfo",
    "cmd_time": "/time",
    "cmd_chatinfo": "/chatinfo",
    "cmd_avatar": "/avatar",
    "cmd_version": "/version",
    "cmd_exit": "/exit"
}

@router.callback_query(F.data.in_(CALLBACK_ACTIONS.keys()))
async def handle_level1_callbacks(callback: CallbackQuery):
    action = CALLBACK_ACTIONS.get(callback.data)
    
    # Если это команда (начинается с /), просим пользователя ввести её
    if action.startswith("/"):
        await callback.answer(f"Для этого используй команду {action}", show_alert=True)
    else:
        # Если это текстовое пояснение
        await callback.answer(action, show_alert=True)