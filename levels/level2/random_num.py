import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()

# Хэндлер инициализации рандомайзера чисел
@router.callback_query(F.data == "cmd_random_num")
async def start_random(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🎲 <b>Рандомайзер (1-N)</b>\n\n"
        "Введите максимальное целое число (N), до которого нужно сгенерировать случайное значение.\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_random_max)
    await callback.answer()


# Хэндлер валидации ввода и генерации случайного числа
@router.message(Level2States.waiting_for_random_max)
async def process_random_max(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Обработка ручной отмены операции
    if text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Генерация числа отменена.")
        return
        
    # Валидация на то то, что введены только цифры
    if not text.isdigit():
        await message.answer("❌ Пожалуйста, введите <b>целое положительное число</b>.", parse_mode="HTML")
        return
        
    # Защита от DoS-атак: ограничиваем длину строки, чтобы int(text) не сожрал память сервера
    if len(text) > 10:
        await message.answer("❌ Число слишком огромное! Максимальное значение: <code>1 000 000 000</code>", parse_mode="HTML")
        return
        
    n = int(text)
    
    # Проверка диапазона
    if n <= 1:
        await message.answer("❌ Число N должно быть больше 1.")
        return
        
    # ЖЕСТКИЙ ЛИМИТ: верхняя граница диапазона для безопасности random.randint
    if n > 1000000000:
        await message.answer("❌ Ошибка! Число N не может превышать 1 000 000 000.")
        return

    # Генерируем случайное значение в безопасном диапазоне
    random_result = random.randint(1, n)
    
    await message.answer(
        f"🎲 Случайное число от 1 до {n}:\n\n"
        f"🎯 Результат: <code>{random_result}</code>",
        parse_mode="HTML"
    )
    await state.clear()