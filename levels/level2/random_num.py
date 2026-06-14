import random
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()

# 1. Ловим клик по кнопке в меню
@router.callback_query(F.data == "cmd_random_num")
async def start_random(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🎲 <b>Рандомайзер (1-N)</b>\n\n"
        "Введите максимальное целое число (N), до которого нужно сгенерировать случайное значение:",
        parse_mode="HTML"
    )
    # Переводим пользователя в состояние ожидания числа
    await state.set_state(Level2States.waiting_for_random_max)
    # Отвечаем на callback, чтобы убрать часики на кнопке в ТГ
    await callback.answer()

# 2. Ловим текстовое сообщение ТОЛЬКО когда пользователь в нужном состоянии
@router.message(Level2States.waiting_for_random_max)
async def process_random_max(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Валидация: проверяем, что введено именно число
    if not text.isdigit():
        await message.answer("❌ Пожалуйста, введите <b>целое положительное число</b>.")
        return
        
    n = int(text)
    
    if n <= 1:
        await message.answer("❌ Число N должно быть больше 1.")
        return

    # Генерируем случайное число от 1 до N
    random_result = random.randint(1, n)
    
    await message.answer(
        f"🎲 Случайное число от 1 до {n}:\n\n"
        f"🎯 Результат: <code>{random_result}</code>",
        parse_mode="HTML"
    )
    
    # Сбрасываем состояние, чтобы бот снова реагировал в обычном режиме
    await state.clear()