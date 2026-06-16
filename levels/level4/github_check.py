import os
import aiohttp
from aiogram import Router, F, html # Импортируем html для защиты от спецсимволов в коммитах
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from config import GITHUB_REPO, ADMIN_ID

router = Router()

# Читаем ID администратора из окружения
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


# Хэндлер проверки последних коммитов в репозитории проекта
@router.callback_query(F.data == "cmd_github_check")
async def check_github_commits(callback: CallbackQuery):
    # Жесткий барьер безопасности: доступ только для создателя бота
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ только для администратора!", show_alert=True)
        return

    if not GITHUB_REPO:
        await callback.message.answer("❌ В .env не заполнена переменная GITHUB_REPO (формат: юзер/репо)")
        await callback.answer()
        return

    # Отправляем статус-сообщение, которое затем обновим (избегаем спама сообщениями)
    status_msg = await callback.message.answer("🔄 Запрашиваю последние коммиты с GitHub...")
    await callback.answer()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    
    # Задаем жесткий таймаут соединения (15 секунд), чтобы бот не зависал при сбоях сети
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # GitHub API строго требует уникальный User-Agent для идентификации запросов
            headers = {"User-Agent": "TelegramBot-App-Monitoring"}
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    commits_data = await response.json()
                    
                    if not commits_data:
                        await status_msg.edit_text("📁 Репозиторий пуст, коммитов не найдено.")
                        return
                    
                    message_text = (
                        f"🐙 <b>Последние обновления в репозитории:</b>\n"
                        f"📦 <code>{html.quote(GITHUB_REPO)}</code>\n\n"
                    )
                    
                    # Берем последние 5 коммитов для вывода в чат
                    for commit in commits_data[:5]:
                        raw_author = commit["commit"]["author"]["name"]
                        raw_message = commit["commit"]["message"].split('\n')[0]
                        sha = commit["sha"][:7]
                        date = commit["commit"]["author"]["date"][:10]
                        
                        # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Экранируем данные, так как в коде и именах часто бывают знаки <, > и &
                        author = html.quote(raw_author)
                        message = html.quote(raw_message)
                        
                        message_text += (
                            f"🔹 <b>{date}</b> - <code>{sha}</code>\n"
                            f"👤 Автор: {author}\n"
                            f"📝 {message}\n\n"
                        )
                    
                    # Обновляем старое техническое сообщение на результат выполнения
                    await status_msg.edit_text(message_text, parse_mode="HTML")
                    
                elif response.status == 403:
                    await status_msg.edit_text("❌ Ошибка API GitHub: Превышен лимит запросов (Rate Limit) для вашего IP.")
                elif response.status == 404:
                    await status_msg.edit_text("❌ Репозиторий не найден. Проверьте правильность GITHUB_REPO в .env.")
                else:
                    await status_msg.edit_text(f"❌ Ошибка API GitHub. Статус-код ответа: {response.status}")
                    
    except Exception as e:
        await status_msg.edit_text(f"❌ Не удалось связаться с серверами GitHub. Ошибка: {e}")