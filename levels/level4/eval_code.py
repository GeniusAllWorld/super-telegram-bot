import os
import sys
import io
import html
import traceback
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level4States

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

@router.callback_query(F.data == "cmd_eval_code")
async def start_eval_console(callback: CallbackQuery, state: FSMContext):
    # Жесткий барьер безопасности
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен! Вы не админ.", show_alert=True)
        return

    await callback.message.answer(
        "🐍 <b>Python Выполнитель кода (Eval/Exec)</b>\n\n"
        "Отправьте мне код на Python. Чтобы увидеть результат, используйте <code>print()</code>.\n\n"
        "<i>Пример:</i>\n"
        "<code>a = 5\nb = 10\nprint(f'Сумма: {a+b}')</code>",
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_eval)
    await callback.answer()

@router.message(Level4States.waiting_for_eval)
async def execute_python_code(message: Message, state: FSMContext):
    # Дублируем проверку безопасности
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return

    code = message.text
    await message.answer("⏳ Выполняю код...")

    # Перенаправляем стандартный вывод (print) в строку, чтобы поймать результат
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    # Создаем изолированное пространство имен для выполнения
    local_variables = {
        "message": message,
        "bot": message.bot,
        "os": os,
        "sys": sys
    }
    
    try:
        # Выполняем многострочный код
        exec(code, {}, local_variables)
        
        # Забираем всё, что код успел «напринтить»
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        
        if not output:
            output = "✅ Код выполнен успешно, но ничего не вывел (нет принтов)."
            
        await message.answer(f"📤 <b>Результат выполнения:</b>\n<code>{html.escape(output)}</code>", parse_mode="HTML")
        
    except Exception:
        # Если код упал, возвращаем полноценный traceback (ошибку)
        sys.stdout = old_stdout
        error_traceback = traceback.format_exc()
        await message.answer(
            f"❌ <b>Ошибка выполнения кода:</b>\n<code>{html.escape(error_traceback)}</code>", 
            parse_mode="HTML"
        )

    await state.clear()