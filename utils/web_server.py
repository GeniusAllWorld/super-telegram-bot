import os
import logging
from aiohttp import web

async def handle_index(request):
    """Явный обработчик для корня сайта — отдаем index.html напрямую"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, 'web', 'index.html')
    return web.FileResponse(index_path)

async def init_web_server():
    """Инициализация веб-сервера с поддержкой корневого index.html"""
    app = web.Application()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = os.path.join(base_dir, 'web')
    
    # 1. Привязываем обработчик для корня '/'
    app.router.add_get('/', handle_index)
    
    # 2. Раздаем все остальные статические файлы (картинки, стили, скрипты)
    app.router.add_static('/', path=web_dir, name='static', follow_symlinks=True)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host='0.0.0.0', port=8080)
    await site.start()
    
    logging.info("🌐 [Web Server] Локальный веб-сервер успешно запущен на http://localhost:8080")