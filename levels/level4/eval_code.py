import os
import sys
import io
import html
import traceback
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level4States

router = Router()

# Читаем ID администратора
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


# Хэндлер инициализации удаленной Python-консоли
@router.callback_query(F.data == "cmd_eval_code")
async def start_eval_console(callback: CallbackQuery, state: FSMContext):
    # Жесткий барьер безопасности
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен! Вы не админ.", show_alert=True)
        return

    await callback.message.answer(
        "🐍 <b>Python Асинхронная REPL-Консоль (Exec)</b>\n\n"
        "Отправьте мне код. Поддерживаются асинхронные вызовы через <code>await</code>.\n"
        "Для вывода используйте <code>print()</code>.\n"
        "Для отмены напишите <b>отмена</b>.\n\n"
        "<i>Пример:</i>\n"
        "<code>await message.answer('Хеллоу!')\n"
        "print('Успешно отправлено')</code>",
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_eval)
    await callback.answer()


# Хэндлер динамического выполнения асинхронного Python-кода
@router.message(Level4States.waiting_for_eval)
async def execute_python_code(message: Message, state: FSMContext):
    # Дублируем проверку безопасности на уровне сообщения
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return

    code = message.text.strip()
    
    # Обработка ручной отмены операции
    if code.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Работа с консолью кода завершена.")
        return

    status_msg = await message.answer("⏳ Выполняю код...")

    # Сохраняем оригинальный поток вывода
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    # Изолированное пространство имен (добавляем модули для удобства админа)
    local_variables = {
        "message": message,
        "bot": message.bot,
        "os": os,
        "sys": sys,
        "asyncio": asyncio
    }
    
    try:
        # ПОФИКСИЛИ АСИНХРОННОСТЬ: Оборачиваем сырой код админа в динамическую асинхронную функцию
        # Это позволяет использовать await прямо внутри сообщения
        wrapped_code = "async def __ex():\n" + "".join(f"    {line}\n" for line in code.splitlines())
        
        # Компилируем и выполняем объявление функции __ex
        exec(wrapped_code, {}, local_variables)
        
        # Достаем готовую корутину из пространства имен
        func = local_variables["__ex"]
        
        # ПОФИКСИЛИ ЗАВИСАНИЕ: Выполняем асинхронную функцию с жестким таймаутом в 5 секунд
        # Если админ напишет бесконечный цикл, таймаут спасет бота от вечного зависания
        await asyncio.wait_for(func(), timeout=5.0)
        
        output = redirected_output.getvalue()
        if not output:
            output = "✅ Код выполнен успешно, пустой вывод stdout."
            
        await status_msg.edit_text(
            f"📤 <b>Результат выполнения:</b>\n<code>{html.escape(output)}</code>", 
            parse_mode="HTML"
        )
        
    except asyncio.TimeoutError:
        # Срабатывает, если код админа выполнялся дольше 5 секунд
        await status_msg.edit_text("❌ <b>Ошибка: Превышен таймаут выполнения (5 секунд)!</b>")
    except Exception:
        # Если код упал с ошибкой, перехватываем трейсбэк
        error_traceback = traceback.format_exc()
        await status_msg.edit_text(
            f"❌ <b>Ошибка выполнения кода:</b>\n<code>{html.escape(error_traceback)}</code>", 
            parse_mode="HTML"
        )
    finally:
        # ПОФИКСИЛИ СБОЙ ПОТОКА: Гарантированно возвращаем стандартный вывод системе
        sys.stdout = old_stdout

    await state.clear()