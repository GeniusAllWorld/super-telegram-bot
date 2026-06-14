import asyncio
import aiohttp
import html
import random
import translators as ts
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.states import Level3States

router = Router()

@router.callback_query(F.data == "cmd_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    # Сообщаем пользователю, что бот генерирует вопрос
    await callback.message.answer("🔄 Загружаю вопрос и перевожу на русский...")
    await callback.answer()
    
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                await callback.message.answer("❌ Не удалось загрузить вопрос. Попробуйте позже.")
                return
                
            data = await response.json()
            question_data = data['results'][0]
            
            # Декодируем HTML-символы
            question_text = html.unescape(question_data['question'])
            correct_answer = html.unescape(question_data['correct_answer'])
            incorrect_answers = [html.unescape(a) for a in question_data['incorrect_answers']]
            
            # Собираем все ответы и перемешиваем их
            all_answers = incorrect_answers + [correct_answer]
            random.shuffle(all_answers)
            
            # --- ХИТРЫЙ ПЕРЕВОД ОДНИМ ЗАПРОСОМ ---
            # Склеиваем вопрос и ответы в один пакет для перевода
            pack_to_translate = f"{question_text}\n" + "\n".join(all_answers)
            
            try:
                translated_pack = await asyncio.to_thread(
                    ts.translate_text,
                    query_text=pack_to_translate,
                    from_language='en',
                    to_language='ru',
                    engine='bing'
                )
                # Разрезаем переведенный пакет обратно на строчки
                translated_lines = translated_pack.split("\n")
                
                ru_question = translated_lines[0]
                ru_answers = translated_lines[1:]
            except Exception as e:
                # Если перевод упал, используем заглушку, чтобы бот не вылетел
                ru_question = " (Ошибка перевода) "
                ru_answers = ["" for _ in all_answers]

            # Сохраняем правильный английский ответ в FSM
            await state.update_data(quiz_correct_answer=correct_answer)
            await state.set_state(Level3States.waiting_for_quiz_answer)
            
            # Формируем красивый текст сообщения с переводом
            message_text = (
                f"🧩 <b>QUIZ / ВИКТОРИНА</b>\n\n"
                f"❓ <b>Вопрос:</b> {question_text}\n"
                f"👉 <i>({ru_question})</i>\n\n"
                f"📋 <b>Варианты ответов (Перевод):</b>\n"
            )
            
            # Добавляем варианты с переводом в текст сообщения
            for eng, ru in zip(all_answers, ru_answers):
                message_text += f"• <b>{eng}</b> — <i>{ru}</i>\n"
            
            # Создаем кнопки строго на английском, как в ТЗ
            builder = InlineKeyboardBuilder()
            for answer in all_answers:
                builder.button(text=answer, callback_data=f"quiz_ans:{answer}")
            builder.adjust(1)
            
            await callback.message.answer(
                message_text, 
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

@router.callback_query(Level3States.waiting_for_quiz_answer, F.data.startswith("quiz_ans:"))
async def check_answer(callback: CallbackQuery, state: FSMContext):
    user_answer = callback.data.split(":", 1)[1]
    data = await state.get_data()
    correct_answer = data.get("quiz_correct_answer")
    
    if user_answer == correct_answer:
        await callback.message.answer(f"✅ <b>Правильно!</b>\n\nОтвет: <code>{correct_answer}</code>",
        parse_mode="HTML")
    else:
        await callback.message.answer(f"❌ <b>Неверно...</b>\n\nПравильный ответ: <code>{correct_answer}</code>",
        parse_mode="HTML")
    
    # Удаляем меню с кнопками после ответа, чтобы пользователь не кликал дважды
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await state.clear()