import asyncio
import aiohttp
import html
import random
import translators as ts
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from utils.states import Level3States

router = Router()


# Хэндлер инициализации викторины и парсинга OpenTDB API
@router.callback_query(F.data == "cmd_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    # Гарантированно очищаем старые состояния перед новой игрой
    await state.clear()
    
    # Информируем пользователя о начале генерации таски
    status_msg = await callback.message.answer("🔄 Загружаю вопрос и перевожу на русский...")
    await callback.answer()
    
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status != 200:
                    await status_msg.edit_text("❌ Не удалось загрузить вопрос от OpenTDB. Попробуйте позже.")
                    return
                    
                data = await response.json()
                
                # Проверяем валидность структуры ответа API
                if not data.get('results'):
                    await status_msg.edit_text("❌ База данных вопросов временно недоступна.")
                    return
                    
                question_data = data['results'][0]
                
                # Декодируем экранированные HTML сущности (&quot;, &#039; и т.д.)
                question_text = html.unescape(question_data['question'])
                correct_answer = html.unescape(question_data['correct_answer'])
                incorrect_answers = [html.unescape(a) for a in question_data['incorrect_answers']]
                
                # Собираем все варианты ответов в единый пул
                all_answers = incorrect_answers + [correct_answer]
                random.shuffle(all_answers)
                
                # Определяем позицию правильного ответа внутри перемешанного массива
                correct_index = all_answers.index(correct_answer)
                
                # Переводим только тело вопроса в неблокирующем потоке для стабильности структуры текста
                try:
                    ru_question = await asyncio.to_thread(
                        ts.translate_text,
                        query_text=question_text,
                        from_language='en',
                        to_language='ru',
                        engine='bing'
                    )
                except Exception:
                    ru_question = "Перевод недоступен."

                # ПОФИКСИЛИ ОШИБКУ 64 БАЙТ: Сохраняем ответы и индекс верного варианта в FSM-контекст
                await state.update_data(
                    quiz_answers=all_answers,
                    quiz_correct_index=correct_index
                )
                await state.set_state(Level3States.waiting_for_quiz_answer)
                
                # Формируем красивый вывод карточки викторины
                message_text = (
                    f"🧩 <b>QUIZ / ВИКТОРИНА</b>\n\n"
                    f"❓ <b>Вопрос:</b> {question_text}\n"
                    f"👉 <i>({ru_question})</i>\n\n"
                    f"📋 <b>Варианты ответов:</b>\n"
                )
                
                for idx, ans in enumerate(all_answers, start=1):
                    message_text += f"{idx}. <b>{ans}</b>\n"
                
                # ПОФИКСИЛИ ИНВАЛИДНОСТЬ ДАННЫХ: Передаем в callback_data только безопасный ID индекса (quiz_ans:0)
                builder = InlineKeyboardBuilder()
                for idx, _ in enumerate(all_answers):
                    builder.button(text=f"{idx + 1}", callback_data=f"quiz_ans:{idx}")
                builder.adjust(4) # Выстраиваем кнопки выбора в один красивый ряд
                
                # Удаляем старый статус загрузки и выкатываем готовую карточку викторины
                await status_msg.delete()
                await callback.message.answer(
                    message_text,
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
                
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Произошла ошибка при подготовке викторины: {e}")
        except Exception:
            await callback.message.answer(f"❌ Произошла ошибка при подготовке викторины: {e}")


# Хэндлер обработки нажатия на кнопку ответа и сверки индексов
@router.callback_query(Level3States.waiting_for_quiz_answer, F.data.startswith("quiz_ans:"))
async def check_answer(callback: CallbackQuery, state: FSMContext):
    # Безопасно парсим ID выбранного индекса ответа
    user_index = int(callback.data.split(":")[1])
    
    # Извлекаем эталонные данные из FSM памяти
    data = await state.get_data()
    all_answers = data.get("quiz_answers", [])
    correct_index = data.get("quiz_correct_index")
    
    # Защита от битой сессии
    if not (jealousy_answers := all_answers):
        await callback.answer("❌ Сессия игры устарела. Начните новую викторину.")
        await state.clear()
        return
        
    correct_answer = jealousy_answers[correct_index]
    user_answer = jealousy_answers[user_index]
    
    # Сверяем индексы ответов
    if user_index == correct_index:
        result_text = f"✅ <b>Правильно!</b>\n\nВы выбрали: <code>{user_answer}</code>"
    else:
        result_text = f"❌ <b>Неверно...</b>\n\nВы выбрали: <code>{user_answer}</code>\n🎯 Правильный ответ: <code>{correct_answer}</code>"
        
    # Сбрасываем стейт до отправки сообщения во избежание двойных кликов
    await state.clear()
    
    # Удаляем инлайн-меню кнопкой, чтобы юзер не мог перевыбрать ответ после завершения
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        # Падаем без ошибок, если сообщение уже удалено
        pass
        
    await callback.message.answer(result_text, parse_mode="HTML")
    await callback.answer()