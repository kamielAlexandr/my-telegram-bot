# test_postgres.py
import os
from database import db

print("🔍 Тестирование подключения к PostgreSQL...")

# Проверяем подключение
try:
    # Пробуем создать тестового пользователя
    test_user_id = 999999
    db.create_user(test_user_id, "test", "Test", "User")
    print("✅ Подключение к PostgreSQL успешно!")
    
    # Получаем пользователя
    user = db.get_user(test_user_id)
    if user:
        print(f"✅ Пользователь получен: {user['user_id']}")
    
    # Тестируем инвентарь
    db.add_to_inventory(test_user_id, "test", "test_item", 5)
    inventory = db.get_inventory(test_user_id)
    print(f"✅ Инвентарь работает: {len(inventory)} предметов")
    
    # Тестируем обновление
    db.update_user(test_user_id, coins=500)
    user = db.get_user(test_user_id)
    print(f"✅ Обновление работает: {user['coins']} монет")
    
    print("\n🎉 Все тесты PostgreSQL прошли успешно!")
    
except Exception as e:
    print(f"❌ Ошибка при тестировании PostgreSQL: {e}")
    import traceback
    traceback.print_exc()
