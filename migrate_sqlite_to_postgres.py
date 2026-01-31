# migrate_sqlite_to_postgres.py
import sqlite3
import os
from database import db

def migrate_data():
    print("🔄 Начинаем миграцию данных из SQLite в PostgreSQL...")
    
    # Подключаемся к SQLite
    if not os.path.exists('game_bot.db'):
        print("❌ Файл SQLite не найден!")
        return
    
    sqlite_conn = sqlite3.connect('game_bot.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # Миграция пользователей
        print("📋 Мигрируем пользователей...")
        sqlite_cursor.execute('SELECT * FROM users')
        users = sqlite_cursor.fetchall()
        
        for user in users:
            user_dict = dict(user)
            db.create_user(
                user_id=user_dict['user_id'],
                username=user_dict.get('username', ''),
                first_name=user_dict.get('first_name', ''),
                last_name=user_dict.get('last_name', '')
            )
            
            # Обновляем остальные данные
            update_data = {}
            for key in ['character_name', 'race', 'level', 'exp', 
                       'exp_to_next_level', 'skill_points', 'coins',
                       'health', 'max_health', 'attack', 'defense',
                       'daily_hunts', 'last_hunt_date']:
                if key in user_dict:
                    update_data[key] = user_dict[key]
            
            if update_data:
                db.update_user(user_dict['user_id'], **update_data)
        
        print(f"✅ Мигрировано {len(users)} пользователей")
        
        # Миграция инвентаря
        print("🎒 Мигрируем инвентарь...")
        sqlite_cursor.execute('SELECT * FROM inventory')
        items = sqlite_cursor.fetchall()
        
        for item in items:
            item_dict = dict(item)
            db.add_to_inventory(
                user_id=item_dict['user_id'],
                item_type=item_dict['item_type'],
                item_name=item_dict['item_name'],
                quantity=item_dict['quantity']
            )
        
        print(f"✅ Мигрировано {len(items)} предметов")
        
        print("\n🎉 Миграция завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_data()
