import os
from aiogram import Router, F
import html
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import text
# Импортируй свою асинхронную сессию/движок, который мы создавали на Уровне 1
# Предположим, она лежит в utils.db или database.connection
from database.db import async_session_maker 
from utils.states import Level4States  # Не забудь добавить state waiting_for_sql в класс Level4States

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

@router.callback_query(F.data == "cmd_sql_console")
async def start_sql_console(callback: CallbackQuery, state: FSMContext):
    # Жесткий барьер для чужаков
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await callback.message.answer(
        "💻 <b>SQL Консоль Администратора</b>\n\n"
        "Отправьте мне валидный SQL-запрос (например: <code>SELECT * FROM users LIMIT 5;</code>):",
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_sql)
    await callback.answer()

@router.message(Level4States.waiting_for_sql)
async def execute_sql_query(message: Message, state: FSMContext):
    # Еще одна проверка на всякий случай
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return

    query_text = message.text
    await message.answer("⏳ Выполняю запрос...")

    try:
        # Открываем сессию SQLAlchemy
        async with async_session_maker() as session:
            async with session.begin():
                # Выполняем сырой SQL через Алхимию
                result = await session.execute(text(query_text))
                
                # Проверяем, вернул ли запрос строки (SELECT) или это был INSERT/UPDATE
                if result.returns_rows:
                    rows = result.all()
                    headers = result.keys()
                    
                    if not rows:
                        await message.answer("ℹ️ Запрос выполнен успешно, но вернул 0 строк.")
                        await state.clear()
                        return
                    
                    # Форматируем результат в красивую текстовую таблицу
                    response = f"📊 <b>Результат ({len(rows)} строк):</b>\n\n"
                    response += f"📌 <code>{' | '.join(headers)}</code>\n"
                    response += "─" * 30 + "\n"
                    
                    for row in rows[:10]:  # Ограничим вывод 10 строками, чтобы не взорвать чат
                        row_str = " | ".join(str(val) for val in row)
                        response += f"▫️ <code>{row_str}</code>\n"
                        
                    if len(rows) > 10:
                        response += f"\n<i>...и еще {len(rows) - 10} строк.</i>"
                else:
                    # Если это был UPDATE/DELETE/INSERT, выводим количество затронутых строк
                    await session.commit()
                    response = f"✅ Запрос успешно выполнен. Затронуто строк: {result.rowcount}"

                await message.answer(response, parse_mode="HTML")

    except Exception as e:
        # Экранируем текст ошибки, чтобы Телеграм не принял её за свои HTML-теги
        safe_error = html.escape(str(e))
        await message.answer(f"❌ <b>Ошибка SQL:</b>\n<code>{safe_error}</code>", parse_mode="HTML")

    await state.clear()