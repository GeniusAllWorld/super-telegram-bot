import os
import logging
from aiohttp import web

# Явный обработчик для корня сайта — отдаем index.html напрямую
async def handle_index(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, 'web', 'index.html')
    return web.FileResponse(index_path)

# Инициализация веб-сервера с поддержкой корневого index.html
async def init_web_server():
    app = web.Application()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = os.path.join(base_dir, 'web')
    
    # 1. Привязываем обработчик для корня '/' (отдает главную страницу Mini App)
    app.router.add_get('/', handle_index)
    
    # 2. Раздаем статические файлы через выделенный префикс '/static'
    # Это предотвращает конфликты маршрутизации в aiohttp.
    # В твоем index.html пути к стилям должны быть вида: /static/css/style.css
    app.router.add_static('/static', path=web_dir, name='static', follow_symlinks=True)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Запуск сервера на всех интерфейсах (важно для работы через ngrok/локалку)
    site = web.TCPSite(runner, host='0.0.0.0', port=8080)
    await site.start()
    
    logging.info("🌐 [Web Server] Локальный веб-сервер успешно запущен на http://localhost:8080")