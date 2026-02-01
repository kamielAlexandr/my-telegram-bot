#!/usr/bin/env python3
import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Healthcheck сервер для Railway
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ Healthcheck сервер запущен на порту {port}")
    server.serve_forever()

# Запускаем healthcheck в фоне
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()

# Ждем 3 секунды чтобы Railway увидел healthcheck
time.sleep(3)

print("🚀 Запускаем Telegram бота...")

# Запускаем основной бот
if __name__ == "__main__":
    # Добавляем путь для импорта
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Импортируем и запускаем бота
    try:
        import bot
        bot.main()
    except ImportError:
        print("❌ Не могу импортировать bot.py")
        print("📂 Текущая директория:", os.getcwd())
        print("📂 Файлы:", os.listdir())
        sys.exit(1)
