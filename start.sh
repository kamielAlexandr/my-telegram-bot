#!/bin/bash
echo "=========================================="
echo "🚀 Запуск Hero's Path Bot на Railway"
echo "=========================================="

# Запускаем веб-сервер для healthcheck в фоне
python3 -m http.server 8080 &
HEALTH_PID=$!

# Даем время Railway проверить healthcheck
sleep 5

# Запускаем бота
python3 main.py

# Если бот упал, убиваем healthcheck сервер
kill $HEALTH_PID 2>/dev/null
