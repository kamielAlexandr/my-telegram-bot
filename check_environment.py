#!/usr/bin/env python3
"""
Проверка окружения на Railway
"""

import os

print("=" * 60)
print("ПРОВЕРКА ОКРУЖЕНИЯ RAILWAY")
print("=" * 60)

# 1. Проверяем наличие ключевых переменных
print("\n1. КЛЮЧЕВЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
print("-" * 40)

env_vars = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'DATABASE_URL': os.environ.get('DATABASE_URL'),
    'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
    'RAILWAY_SERVICE_NAME': os.environ.get('RAILWAY_SERVICE_NAME'),
    'RAILWAY_PROJECT_NAME': os.environ.get('RAILWAY_PROJECT_NAME'),
}

for key, value in env_vars.items():
    status = "✅ УСТАНОВЛЕНА" if value else "❌ НЕ УСТАНОВЛЕНА"
    
    if value and any(s in key.lower() for s in ['token', 'pass', 'secret', 'url']):
        # Скрываем часть значения для безопасности
        display_value = value[:20] + "..." if len(value) > 20 else value[:3] + "***"
        print(f"{key}: {status} -> {display_value}")
    else:
        print(f"{key}: {status} -> {value}")

# 2. Проверяем наличие других переменных
print("\n2. ВСЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
print("-" * 40)

for key in sorted(os.environ.keys()):
    value = os.environ[key]
    if any(s in key.lower() for s in ['token', 'pass', 'secret', 'key']):
        value = '***СКРЫТО***'
    print(f"{key} = {value}")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИИ:")
print("=" * 60)

if not env_vars['BOT_TOKEN']:
    print("1. ❌ Добавьте BOT_TOKEN в Variables на Railway")
    print("   - Получите токен у @BotFather в Telegram")

if not env_vars['DATABASE_URL']:
    print("2. ❌ Добавьте DATABASE_URL в Variables на Railway")
    print("   - Создайте базу: Railway Dashboard -> New -> Database")
    print("   - Или добавьте вручную: Connection URL из раздела Database")

if env_vars['RAILWAY_ENVIRONMENT']:
    print(f"3. ✅ Работаем на Railway: {env_vars['RAILWAY_ENVIRONMENT']}")
else:
    print("3. ⚠️  Локальная разработка")

print("\n" + "=" * 60)
