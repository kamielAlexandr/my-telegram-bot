# database.py
import sqlite3
import os
import datetime
import shutil
import glob

class Database:
    def __init__(self, db_path='data/game_bot.db'):
        self.db_path = db_path
        self.data_dir = os.path.dirname(db_path)
        
        # Создаем папку для данных, если ее нет
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 Создана папка для данных: {self.data_dir}")
        
        # Создаем резервную копию
        self.create_backup()
        
        # Инициализируем БД
        self.init_db()
    
    def create_backup(self):
        """Создание резервной копии базы данных"""
        try:
            if os.path.exists(self.db_path):
                # Создаем папку для бэкапов
                backup_dir = 'backups'
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Формируем имя файла
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{backup_dir}/game_bot_{timestamp}.db"
                
                # Копируем файл
                shutil.copy2(self.db_path, backup_name)
                print(f"✅ Резервная копия создана: {backup_name}")
                
                # Удаляем старые бэкапы
                self.cleanup_old_backups(backup_dir)
                
                return backup_name
            else:
                print("🆕 База данных не найдена, будет создана новая")
        except Exception as e:
            print(f"⚠️ Не удалось создать резервную копию: {e}")
        return None
    
    def cleanup_old_backups(self, backup_dir, keep_last=5):
        """Удаление старых резервных копий"""
        try:
            backup_files = glob.glob(f"{backup_dir}/game_bot_*.db")
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            if len(backup_files) > keep_last:
                for file in backup_files[keep_last:]:
                    os.remove(file)
                    print(f"🗑️ Удален старый бэкап: {file}")
        except Exception as e:
            print(f"⚠️ Не удалось очистить старые бэкапы: {e}")
    
    def get_connection(self):
        """Создаем соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Включаем поддержку внешних ключей
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    character_name TEXT,
                    race TEXT,
                    level INTEGER DEFAULT 1,
                    exp INTEGER DEFAULT 0,
                    exp_to_next_level INTEGER DEFAULT 100,
                    skill_points INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    attack INTEGER DEFAULT 10,
                    defense INTEGER DEFAULT 5,
                    daily_hunts INTEGER DEFAULT 0,
                    last_hunt_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица инвентаря
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_type TEXT,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            
            # Проверяем состояние БД
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_count = cursor.fetchone()[0]
            
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            print(f"✅ База данных инициализирована")
            print(f"   📊 Пользователей: {user_count}")
            print(f"   📏 Размер файла: {file_size} байт")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                conn.close()
    
    # Остальные методы остаются без изменений
    def get_user(self, user_id):
        """Получение данных пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    # ... добавьте все остальные методы из вашего кода ...
