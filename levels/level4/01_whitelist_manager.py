import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update
from database.db import async_session_maker
from database.models import User  # Импортируй свою модель User правильно
from utils.states import Level4States
from config import ADMIN_ID

router = Router()

# Клавиатура управления белым списком
def get_whitelist_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить ID", callback_data="wl_add"),
            InlineKeyboardButton(text="➖ Удалить ID", callback_data="wl_remove")
        ]
    ])

# 1. Вывод текущего белого списка
@router.callback_query(F.data == "cmd_whitelist_manager")
async def show_whitelist(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    async with async_session_maker() as session:
        # Ищем всех пользователей, у которых флаг равен True
        query = select(User).where(User.is_whitelisted == True)
        result = await session.execute(query)
        whitelisted_users = result.scalars().all()

    text = "📃 <b>Белый список пользователей (Whitelist)</b>\n\n"
    if not whitelisted_users:
        text += "<i>Список пуст. Все новые пользователи заблокированы.</i>"
    else:
        for idx, u in enumerate(whitelisted_users, 1):
            username_str = f"(@{u.username})" if u.username else ""
            text += f"{idx}. <code>{u.telegram_id}</code> {username_str}\n"

    text += "\n Выберите действие ниже:"
    await callback.message.answer(text, reply_markup=get_whitelist_kb(), parse_mode="HTML")
    await callback.answer()

# 2. Переход в режим добавления ID
@router.callback_query(F.data == "wl_add")
async def wl_add_trigger(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите <b>Telegram ID</b> пользователя, которого хотите ДОБАВИТЬ в белый список:")
    await state.set_state(Level4States.waiting_for_wl_add)
    await callback.answer()

# 3. Обработка ввода для ДОБАВЛЕНИЯ
@router.message(Level4States.waiting_for_wl_add)
async def process_wl_add(message: Message, state: FSMContext):
    target_id_str = message.text.strip()
    
    if not target_id_str.isdigit():
        await message.answer("⚠️ ID должен состоять только из цифр! Попробуйте еще раз.")
        return

    target_id = int(target_id_str)

    async with async_session_maker() as session:
        async with session.begin():
            # Проверяем, есть ли вообще такой юзер в нашей базе
            query = select(User).where(User.telegram_id == target_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                # Если юзера нет, мы можем сразу создать для него запись авансом
                user = User(telegram_id=target_id, is_whitelisted=True)
                session.add(user)
                await message.answer(f"✅ Пользователь <code>{target_id}</code> не был найден в базе, поэтому я создал новую запись и добавил его в Whitelist!", parse_mode="HTML")
            else:
                user.is_whitelisted = True
                await message.answer(f"✅ Статус пользователя <code>{target_id}</code> успешно обновлен на Whitelist!", parse_mode="HTML")

    await state.clear()

# 4. Переход в режим удаления ID
@router.callback_query(F.data == "wl_remove")
async def wl_remove_trigger(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите <b>Telegram ID</b> пользователя, которого хотите УДАЛИТЬ из белого списка:")
    await state.set_state(Level4States.waiting_for_wl_remove)
    await callback.answer()

# 5. Обработка ввода для УДАЛЕНИЯ
@router.message(Level4States.waiting_for_wl_remove)
async def process_wl_remove(message: Message, state: FSMContext):
    target_id_str = message.text.strip()
    
    if not target_id_str.isdigit():
        await message.answer("⚠️ ID должен состоять только из цифр! Попробуйте еще раз.")
        return

    target_id = int(target_id_str)

    async with async_session_maker() as session:
        async with session.begin():
            query = select(User).where(User.telegram_id == target_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user or not user.is_whitelisted:
                await message.answer("❌ Данный пользователь и так отсутствует в белом списке.")
            else:
                user.is_whitelisted = False
                await message.answer(f"❌ Пользователь <code>{target_id}</code> успешно удален из белого списка.", parse_mode="HTML")

    await state.clear()