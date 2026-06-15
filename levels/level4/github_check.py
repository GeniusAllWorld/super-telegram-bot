import os
import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import GITHUB_REPO, ADMIN_ID

router = Router()

@router.callback_query(F.data == "cmd_github_check")
async def check_github_commits(callback: CallbackQuery):
    # Жесткая проверка на админа
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ только для администратора!", show_alert=True)
        return

    if not GITHUB_REPO:
        await callback.message.answer("❌ В .env не заполнена переменная GITHUB_REPO (формат: юзер/репо)")
        await callback.answer()
        return

    await callback.message.answer("🔄 Запрашиваю последние коммиты с GitHub...")
    await callback.answer()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    
    # Отправляем асинхронный GET-запрос к публичному API GitHub
    async with aiohttp.ClientSession() as session:
        # GitHub API требует указывать User-Agent
        headers = {"User-Agent": "TelegramBot-App"}
        async with session.get(url, headers=headers) as response:
            
            if response.status == 200:
                commits_data = await response.json()
                
                if not commits_data:
                    await callback.message.answer("📁 Репозиторий пуст, коммитов не найдено.")
                    return
                
                message_text = f"🐙 <b>Последние обновления в репозитории:</b>\n" \
                               f"📦 <code>{GITHUB_REPO}</code>\n\n"
                
                # Берем последние 5 коммитов
                for commit in commits_data[:5]:
                    author = commit["commit"]["author"]["name"]
                    message = commit["commit"]["message"].split('\n')[0]  # Только первая строка сообщения
                    sha = commit["sha"][:7]  # Короткий хэш коммита
                    date = commit["commit"]["author"]["date"][:10]  # Дата YYYY-MM-DD
                    
                    message_text += f"🔹 <b>{date}</b> - <code>{sha}</code>\n" \
                                    f"👤 Автор: {author}\n" \
                                    f"📝 {message}\n\n"
                                    
                await callback.message.answer(message_text, parse_mode="HTML")
            else:
                await callback.message.answer(f"❌ Ошибка API GitHub. Статус: {response.status}")