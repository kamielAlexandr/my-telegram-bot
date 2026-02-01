#!/usr/bin/env python3
"""
Менеджер для запуска Telegram бота с защитой от конфликтов 409
"""
import os
import sys
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# Получаем токен бота
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не установлен!")
    sys.exit(1)

class HealthHandler(BaseHTTPRequestHandler):
    """Обработчик healthcheck запросов"""
    def do_GET(self):
        if self.path in ['/', '/health', '/ping']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, *args):
        pass  # Отключаем логирование

def kill_other_instances():
    """Убивает другие экземпляры бота через Telegram API"""
    print("🔄 Завершаем другие сессии бота...")
    
    # Метод 1: Закрываем webhook (если был установлен)
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/close",
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Webhook закрыт")
    except:
        pass
    
    # Метод 2: Устанавливаем webhook в пустую строку
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": ""},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Webhook сброшен")
    except:
        pass
    
    # Метод 3: Получаем текущие обновления с большим offset
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            json={"offset": 999999999, "timeout": 1},
            timeout=10
        )
        print("✅ Текущая сессия завершена")
    except Exception as e:
        print(f"⚠️ Ошибка при завершении: {e}")

def run_health_server(port=8080):
    """Запускает сервер для healthcheck Railway"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        print(f"✅ Healthcheck сервер запущен на порту {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка healthcheck сервера: {e}")

def start_bot():
    """Запускает основного бота"""
    # Даем время healthcheck серверу запуститься
    time.sleep(2)
    
    # Импортируем и запускаем основную логику бота
    try:
        from main import main as bot_main
        
        # Запускаем бота с обработкой ошибок
        while True:
            try:
                print("🚀 Запускаем Telegram бота...")
                bot_main()  # Ваша основная функция
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Ошибка бота: {error_msg}")
                
                # Если это ошибка 409, ждем и перезапускаем
                if "409" in error_msg or "Conflict" in error_msg:
                    print("⚠️ Конфликт обнаружен. Завершаем другие сессии...")
                    kill_other_instances()
                    print("🔄 Перезапуск через 5 секунд...")
                    time.sleep(5)
                else:
                    print("🔄 Перезапуск через 10 секунд...")
                    time.sleep(10)
    except ImportError as e:
        print(f"❌ Не могу импортировать main.py: {e}")
        sys.exit(1)

def main():
    """Основная функция менеджера"""
    print("=======================================")
    print("🤖 Менеджер запуска Hero's Path Bot")
    print("=======================================")
    
    # Шаг 1: Убиваем другие экземпляры
    kill_other_instances()
    
    # Шаг 2: Запускаем healthcheck сервер в отдельном потоке
    port = int(os.environ.get("PORT", 8080))
    health_thread = threading.Thread(
        target=run_health_server,
        args=(port,),
        daemon=True
    )
    health_thread.start()
    
    # Шаг 3: Запускаем бота
    time.sleep(1)
    start_bot()

if __name__ == "__main__":
    main()
