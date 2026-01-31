import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    def __init__(self):
        # Получаем URL базы данных из переменных окружения
        # Railway может использовать разные имена, проверим несколько вариантов
        self.database_url = None
        possible_names = ['DATABASE_URL', 'POSTGRES_URL', 'POSTGRESQL_URL']
        
        for name in possible_names:
            self.database_url = os.environ.get(name)
            if self.database_url:
                logger.info(f"✅ Найдена переменная {name}")
                break
        
        if not self.database_url:
            logger.error("❌ Не найдена переменная с URL базы данных. Проверенные имена: " + ", ".join(possible_names))
            # Выведем все переменные окружения для отладки (без значений, чтобы не было утечек)
            env_keys = list(os.environ.keys())
            logger.info(f"📝 Доступные переменные окружения: {', '.join(env_keys)}")
            # Не будем падать, но будем работать без БД?
            # Для Railway лучше упасть, чтобы увидеть ошибку в логах.
            raise ValueError("Не установлена переменная DATABASE_URL")
        
        # Исправляем формат URL для psycopg2
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info(f"✅ Подключение к БД: {self.database_url[:50]}...")
        
        # Пытаемся подключиться с повторными попытками
        self.retry_connection()
    
    def retry_connection(self):
        """Повторные попытки подключения к БД"""
        max_retries = 5
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                self.init_db()
                logger.info(f"✅ База данных успешно инициализирована (попытка {attempt + 1})")
                return True
            except Exception as e:
                logger.error(f"❌ Попытка {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ Не удалось подключиться к базе данных после всех попыток")
                    # Не выбрасываем исключение, чтобы бот мог продолжить работу
                    # и попробовать подключиться позже
                    return False
    
    def get_connection(self):
        """Создать подключение к PostgreSQL"""
        try:
            conn = psycopg2.connect(
                self.database_url,
                cursor_factory=DictCursor,
                connect_timeout=10
            )
            return conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    def init_db(self):
        """Инициализация таблиц"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Таблица пользователей
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id BIGINT PRIMARY KEY,
                            username VARCHAR(255),
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            character_name VARCHAR(255),
                            race VARCHAR(50),
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
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            item_type VARCHAR(100),
                            item_name VARCHAR(255),
                            quantity INTEGER DEFAULT 1,
                            UNIQUE(user_id, item_type, item_name),
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                        )
                    ''')
                    
                    # Автоматически добавляем отсутствующие столбцы
                    self.add_missing_columns(cursor)
                    
                    # Индексы для производительности
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_users_character_name 
                        ON users(character_name)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_users_level 
                        ON users(level DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_inventory_user 
                        ON inventory(user_id)
                    ''')
                    
                    conn.commit()
                    logger.info("✅ Таблицы базы данных созданы/проверены")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    def add_missing_columns(self, cursor):
        """Добавить отсутствующие столбцы в таблицу users"""
        columns_to_check = [
            ('exp_to_next_level', 'INTEGER DEFAULT 100'),
            ('skill_points', 'INTEGER DEFAULT 0'),
            ('daily_hunts', 'INTEGER DEFAULT 0'),
            ('last_hunt_date', 'DATE DEFAULT CURRENT_DATE')
        ]
        
        for column_name, column_type in columns_to_check:
            try:
                cursor.execute(f'''
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='{column_name}'
                ''')
                if not cursor.fetchone():
                    cursor.execute(f'''
                        ALTER TABLE users 
                        ADD COLUMN {column_name} {column_type}
                    ''')
                    logger.info(f"✅ Добавлен столбец {column_name}")
            except Exception as e:
                logger.warning(f"⚠️  Не удалось добавить столбец {column_name}: {e}")
    
    # ... остальные методы без изменений ...

# Создаем глобальный экземпляр
db = PostgreSQLDatabase()
