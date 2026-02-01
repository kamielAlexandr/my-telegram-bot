#!/bin/bash
echo "======================================="
echo "🚀 Запуск Hero's Path Bot на Railway"
echo "======================================="

# Убиваем возможные предыдущие процессы
pkill -f "python.*main.py" || true
pkill -f "python.*telebot" || true

# Ждем завершения процессов
sleep 3

# Запускаем через менеджер
python bot_manager.py
