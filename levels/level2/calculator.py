from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States
from simpleeval import simple_eval, InvalidExpression

router = Router()

@router.callback_query(F.data == "cmd_calculator")
async def start_calculator(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🧮 <b>Математический калькулятор</b>\n\n"
        "Отправьте мне любое математическое выражение.\n"
        "Можно использовать: <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, скобки и степени <code>**</code>\n\n"
        "Например: <code>(12 + 8) * 5 / 2</code>",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_calc_expression)
    await callback.answer()


@router.message(Level2States.waiting_for_calc_expression)
async def process_calculator(message: Message, state: FSMContext):
    expression = message.text.strip()
    
    try:
        # Безопасно вычисляем выражение из строки
        # Ограничиваем время выполнения, чтобы юзер не прислал бесконечный расчет типа 999999**999999
        result = simple_eval(expression)
        
        # Красиво форматируем результат (убираем .0, если число целое)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
            
        await message.answer(
            f"📊 <b>Результат вычисления:</b>\n\n"
            f"🔢 Выражение: <code>{expression}</code>\n"
            f"🎯 Ответ: <b><code>{result}</code></b>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except ZeroDivisionError:
        await message.answer("❌ Ошибка: Деление на ноль невозможно! Попробуйте еще раз:")
        
    except (InvalidExpression, Exception):
        await message.answer(
            "❌ <b>Неверное выражение!</b>\n"
            "Пожалуйста, используйте только числа и знаки <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>**</code>.\n\n"
            "Попробуйте ввести выражение заново:", 
            parse_mode="HTML"
        )