import os
import html # Используется для тотального экранирования данных таблиц
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import text
from database.db import async_session_maker 
from utils.states import Level4States

router = Router()

# Читаем ID администратора из переменных окружения
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


# Хэндлер инициализации низкоуровневой SQL-консоли
@router.callback_query(F.data == "cmd_sql_console")
async def start_sql_console(callback: CallbackQuery, state: FSMContext):
    # Жесткий барьер безопасности
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await callback.message.answer(
        "💻 <b>SQL Консоль Администратора</b>\n\n"
        "Отправьте мне валидный сырой SQL-запрос для выполнения в БД.\n"
        "Для отмены операции напишите <b>отмена</b>.\n\n"
        "<i>Пример:</i>\n"
        "<code>SELECT telegram_id, username FROM users LIMIT 5;</code>",
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_sql)
    await callback.answer()


# Хэндлер выполнения сырых SQL-запросов и безопасного форматирования ответов
@router.message(Level4States.waiting_for_sql)
async def execute_sql_query(message: Message, state: FSMContext):
    # Повторная проверка прав доступа
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return

    query_text = message.text.strip()
    
    # Обработка ручной отмены операции админом
    if query_text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Работа с SQL-консолью отменена.")
        return

    status_msg = await message.answer("⏳ Выполняю запрос...")

    try:
        # Открываем сессию SQLAlchemy
        async with async_session_maker() as session:
            # ПОФИКСИЛИ КОНФЛИКТ: убран дублирующий контекст session.begin()
            # Будем управлять транзакцией вручную через явный коммит
            result = await session.execute(text(query_text))
            
            # Проверяем, вернул ли запрос строки (SELECT) или это был модифицирующий запрос (INSERT/UPDATE/DELETE)
            if result.returns_rows:
                rows = result.all()
                headers = result.keys()
                
                if not rows:
                    await status_msg.edit_text("ℹ️ Запрос выполнен успешно, но вернул 0 строк.")
                    await state.clear()
                    return
                
                # Форматируем заголовки колонок, защищая их от HTML-краша
                safe_headers = " | ".join(html.escape(str(h)) for h in headers)
                response = f"📊 <b>Результат ({len(rows)} строк):</b>\n\n"
                response += f"📌 <code>{safe_headers}</code>\n"
                response += "─" * 30 + "\n"
                
                # Ограничиваем вывод 10 строками, чтобы не превысить лимит длины сообщения Telegram (4096 символов)
                for row in rows[:10]:
                    # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Экранируем абсолютно каждое значение из БД
                    # Это защищает парсер бота, если в базе хранятся знаки <, > или &
                    row_str = " | ".join(html.escape(str(val)) for val in row)
                    response += f"▫️ <code>{row_str}</code>\n"
                    
                if len(rows) > 10:
                    response += f"\n<i>...и еще {len(rows) - 10} строк.</i>"
            else:
                # Для UPDATE/DELETE/INSERT фиксируем транзакцию в БД
                await session.commit()
                response = f"✅ Запрос успешно выполнен.\nЗатронуто строк (Rowcount): <code>{result.rowcount}</code>"

            await status_msg.edit_text(response, parse_mode="HTML")

    except Exception as e:
        # Экранируем текст ошибки, защищая парсер от краша
        safe_error = html.escape(str(e))
        await status_msg.edit_text(f"❌ <b>Ошибка SQL:</b>\n<code>{safe_error}</code>", parse_mode="HTML")

    await state.clear()