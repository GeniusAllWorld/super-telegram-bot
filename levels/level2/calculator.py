from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States
from simpleeval import SimpleEval, InvalidExpression

router = Router()

# Хэндлер инициализации математического калькулятора
@router.callback_query(F.data == "cmd_calculator")
async def start_calculator(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🧮 <b>Математический калькулятор</b>\n\n"
        "Отправьте мне любое математическое выражение.\n"
        "Можно использовать: <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, скобки и степени <code>**</code>\n\n"
        "Для выхода напишите <b>отмена</b>.\n\n"
        "Например: <code>(12 + 8) * 5 / 2</code>",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_calc_expression)
    await callback.answer()


# Хэндлер безопасного вычисления математического выражения
@router.message(Level2States.waiting_for_calc_expression)
async def process_calculator(message: Message, state: FSMContext):
    expression = message.text.strip()
    
    # Обработка ручной отмены операции
    if expression.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Вычисление отменено.")
        return

    try:
        # Инициализируем безопасный вычислитель simpleeval
        evaluator = SimpleEval()
        
        # ЖЕСТКИЙ ЛИМИТ: Ограничиваем максимальную длину чисел и операторов, 
        # чтобы предотвратить DoS-атаку через гигантские степени (например, 9999**9999)
        evaluator.MAX_POWER = 1000  # Запрещаем возведение в степень выше 1000
        evaluator.MAX_STRING_LENGTH = 100
        
        # Вычисляем результат
        result = evaluator.eval(expression)
        
        # Красиво форматируем результат (убираем .0, если число получилось целым)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
            
        # Защита от слишком длинного ответа (чтобы не упасть на лимитах Telegram в 4096 символов)
        formatted_result = str(result)
        if len(formatted_result) > 300:
            formatted_result = formatted_result[:300] + "... [Число слишком длинное]"
            
        await message.answer(
            f"📊 <b>Результат вычисления:</b>\n\n"
            f"🔢 Выражение: <code>{expression}</code>\n"
            f"🎯 Ответ: <b><code>{formatted_result}</code></b>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except ZeroDivisionError:
        await message.answer("❌ Ошибка: Деление на ноль невозможно! Попробуйте еще раз или напишите 'отмена':")
        
    except (InvalidExpression, Exception):
        await message.answer(
            "❌ <b>Неверное выражение!</b>\n"
            "Пожалуйста, используйте только числа и знаки <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>**</code>.\n\n"
            "Попробуйте ввести выражение заново или напишите 'отмена':", 
            parse_mode="HTML"
        )