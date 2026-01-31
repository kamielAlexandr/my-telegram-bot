# database.py
import os
import psycopg2
from psycopg2.extras import DictCursor, RealDictCursor
from contextlib import contextmanager
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    def __init__(self):
        """Инициализация подключения к PostgreSQL"""
        # Получаем строку подключения из переменных окружения
        self.database_url = os.environ.get('DATABASE_URL')
        
        if not self.database_url:
            logger.error("❌ ОШИБКА: DATABASE_URL не установлена!")
            logger.info("ℹ️ Установите переменную окружения DATABASE_URL в Railway")
            logger.info("ℹ️ Или создайте файл .env с DATABASE_URL=postgresql://...")
            raise ValueError("DATABASE_URL не установлена")
        
        # Конвертируем postgres:// в postgresql:// для psycopg2
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
            logger.info("✅ Конвертирован URL из postgres:// в postgresql://")
        
        logger.info(f"📊 Используется PostgreSQL база данных")
        
        # Тестируем подключение и инициализируем таблицы
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к базе данных"""
        conn = None
        try:
            # Устанавливаем соединение с PostgreSQL
            conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor,
                sslmode='require'  # Требуем SSL для безопасности
            )
            conn.autocommit = False
            yield conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, conn=None):
        """Контекстный менеджер для курсора"""
        if conn is None:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    yield cursor, conn
        else:
            with conn.cursor() as cursor:
                yield cursor, conn
    
    def init_db(self):
        """Инициализация таблиц в PostgreSQL"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    
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
                            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            -- Индексы для быстрого поиска
                            CONSTRAINT valid_health CHECK (health >= 0 AND health <= max_health)
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
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            FOREIGN KEY (user_id) 
                                REFERENCES users(user_id) 
                                ON DELETE CASCADE,
                            
                            -- Уникальность комбинации user_id + item_type + item_name
                            UNIQUE(user_id, item_type, item_name)
                        )
                    ''')
                    
                    # Таблица истории боёв (опционально)
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS battle_history (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            monster_name VARCHAR(255),
                            result VARCHAR(50),
                            rounds INTEGER,
                            exp_gained INTEGER,
                            coins_gained INTEGER,
                            health_lost INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            FOREIGN KEY (user_id) 
                                REFERENCES users(user_id) 
                                ON DELETE CASCADE
                        )
                    ''')
                    
                    # Создаём индексы для ускорения запросов
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_users_race ON users(race)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_users_level ON users(level DESC)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory(user_id)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_inventory_item ON inventory(item_type, item_name)
                    ''')
                    cursor.execute('''
                        CREATE INDEX IF NOT EXISTS idx_battle_history_user ON battle_history(user_id, created_at DESC)
                    ''')
                    
                    # Триггер для автоматического обновления updated_at
                    cursor.execute('''
                        CREATE OR REPLACE FUNCTION update_updated_at_column()
                        RETURNS TRIGGER AS $$
                        BEGIN
                            NEW.updated_at = CURRENT_TIMESTAMP;
                            RETURN NEW;
                        END;
                        $$ language 'plpgsql'
                    ''')
                    
                    cursor.execute('''
                        CREATE TRIGGER update_inventory_updated_at 
                        BEFORE UPDATE ON inventory
                        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
                    ''')
                    
                    conn.commit()
                    logger.info("✅ Таблицы PostgreSQL успешно инициализированы")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации таблиц PostgreSQL: {e}")
            raise
    
    # ================== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==================
    
    def get_user(self, user_id):
        """Получить пользователя по ID"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute(
                        'SELECT * FROM users WHERE user_id = %s',
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя {user_id}: {e}")
            return None
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        """Создать нового пользователя"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        INSERT INTO users 
                        (user_id, username, first_name, last_name, exp_to_next_level) 
                        VALUES (%s, %s, %s, %s, 100)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            last_active = CURRENT_TIMESTAMP
                    ''', (user_id, username, first_name, last_name))
                    
                    conn.commit()
                    logger.info(f"✅ Создан/обновлен пользователь: {user_id}")
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании пользователя {user_id}: {e}")
            return False
    
    def update_user(self, user_id, **kwargs):
        """Обновить данные пользователя"""
        if not kwargs:
            return False
        
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    # Формируем динамический запрос
                    set_fields = []
                    values = []
                    
                    for key, value in kwargs.items():
                        set_fields.append(f"{key} = %s")
                        values.append(value)
                    
                    values.append(user_id)
                    
                    query = f'''
                        UPDATE users 
                        SET {', '.join(set_fields)}, last_active = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    '''
                    
                    cursor.execute(query, values)
                    conn.commit()
                    
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении пользователя {user_id}: {e}")
            return False
    
    def complete_character_creation(self, user_id, character_name, race):
        """Завершить создание персонажа"""
        try:
            race_bonuses = {
                'human': {'attack': 2, 'defense': 2, 'health': 20},
                'elf': {'attack': 5, 'defense': 0, 'health': 10},
                'orc': {'attack': 8, 'defense': 3, 'health': 30},
                'dwarf': {'attack': 3, 'defense': 8, 'health': 25}
            }
            
            if race in race_bonuses:
                bonus = race_bonuses[race]
                return self.update_user(
                    user_id,
                    character_name=character_name,
                    race=race,
                    attack=10 + bonus['attack'],
                    defense=5 + bonus['defense'],
                    health=100 + bonus['health'],
                    max_health=100 + bonus['health'],
                    coins=100
                )
            
            return self.update_user(
                user_id, 
                character_name=character_name, 
                race=race
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при создании персонажа: {e}")
            return False
    
    # ================== МЕТОДЫ ДЛЯ ОПЫТА И УРОВНЕЙ ==================
    
    def add_exp(self, user_id, exp_amount):
        """Добавить опыт пользователю"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            skill_points_gained = 0
            
            # Проверяем повышение уровня
            while new_exp >= user['exp_to_next_level']:
                new_exp -= user['exp_to_next_level']
                new_level += 1
                skill_points_gained += 1
                exp_to_next = int(100 * (1.5 ** (new_level - 1)))
                
                # Обновляем пользователя
                self.update_user(
                    user_id,
                    level=new_level,
                    exp=new_exp,
                    exp_to_next_level=exp_to_next,
                    skill_points=user['skill_points'] + skill_points_gained
                )
                
                # Получаем обновленные данные
                user = self.get_user(user_id)
            
            # Если опыта добавилось, но уровней не прибавилось
            if exp_amount > 0 and skill_points_gained == 0:
                return self.update_user(user_id, exp=new_exp)
            
            return skill_points_gained > 0
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении опыта: {e}")
            return False
    
    # ================== МЕТОДЫ ДЛЯ ИНВЕНТАРЯ ==================
    
    def add_to_inventory(self, user_id, item_type, item_name, quantity=1):
        """Добавить предмет в инвентарь"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        INSERT INTO inventory 
                        (user_id, item_type, item_name, quantity) 
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, item_type, item_name) 
                        DO UPDATE SET 
                            quantity = inventory.quantity + EXCLUDED.quantity,
                            updated_at = CURRENT_TIMESTAMP
                    ''', (user_id, item_type, item_name, quantity))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении в инвентарь: {e}")
            return False
    
    def get_inventory(self, user_id):
        """Получить инвентарь пользователя"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        SELECT item_type, item_name, quantity 
                        FROM inventory 
                        WHERE user_id = %s AND quantity > 0
                        ORDER BY item_type, item_name
                    ''', (user_id,))
                    
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении инвентаря: {e}")
            return []
    
    def use_item(self, user_id, item_type, item_name):
        """Использовать предмет из инвентаря"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    # Проверяем наличие предмета
                    cursor.execute('''
                        SELECT quantity FROM inventory 
                        WHERE user_id = %s AND item_type = %s AND item_name = %s
                        FOR UPDATE
                    ''', (user_id, item_type, item_name))
                    
                    item = cursor.fetchone()
                    
                    if not item or item['quantity'] < 1:
                        return False
                    
                    # Если предмет последний, удаляем строку
                    if item['quantity'] == 1:
                        cursor.execute('''
                            DELETE FROM inventory 
                            WHERE user_id = %s AND item_type = %s AND item_name = %s
                        ''', (user_id, item_type, item_name))
                    else:
                        # Уменьшаем количество
                        cursor.execute('''
                            UPDATE inventory 
                            SET quantity = quantity - 1,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND item_type = %s AND item_name = %s
                        ''', (user_id, item_type, item_name))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка при использовании предмета: {e}")
            return False
    
    # ================== ДРУГИЕ МЕТОДЫ ==================
    
    def add_coins(self, user_id, coins_amount):
        """Добавить монеты пользователю"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        UPDATE users 
                        SET coins = GREATEST(0, coins + %s),
                            last_active = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    ''', (coins_amount, user_id))
                    
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении монет: {e}")
            return False
    
    def use_skill_point(self, user_id, stat):
        """Использовать очко навыка"""
        try:
            user = self.get_user(user_id)
            if not user or user['skill_points'] < 1:
                return False
            
            improvements = {
                'attack': {'attack': user['attack'] + 2},
                'defense': {'defense': user['defense'] + 2},
                'health': {
                    'max_health': user['max_health'] + 15,
                    'health': min(user['health'] + 15, user['max_health'] + 15)
                }
            }
            
            if stat not in improvements:
                return False
            
            improvement = improvements[stat]
            improvement['skill_points'] = user['skill_points'] - 1
            
            return self.update_user(user_id, **improvement)
        except Exception as e:
            logger.error(f"❌ Ошибка при использовании очка навыка: {e}")
            return False
    
    def can_hunt_today(self, user_id):
        """Проверить, может ли пользователь охотиться сегодня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0, 5
            
            today = datetime.now().date()
            last_hunt_date = user['last_hunt_date']
            
            # Если дата последней охоты не сегодня, сбрасываем счетчик
            if not last_hunt_date or last_hunt_date != today:
                self.update_user(user_id, daily_hunts=0, last_hunt_date=today)
                return True, 0, 5
            
            return user['daily_hunts'] < 5, user['daily_hunts'], 5
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке охоты: {e}")
            return False, 0, 5
    
    def increment_daily_hunts(self, user_id):
        """Увеличить счетчик охот"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            today = datetime.now().date()
            
            if user['last_hunt_date'] != today:
                return self.update_user(
                    user_id, 
                    daily_hunts=1, 
                    last_hunt_date=today
                )
            
            return self.update_user(
                user_id, 
                daily_hunts=user['daily_hunts'] + 1
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при увеличении счетчика охот: {e}")
            return False
    
    def get_top_players(self, limit=5):
        """Получить топ игроков"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        SELECT 
                            character_name, 
                            race, 
                            level, 
                            exp, 
                            coins, 
                            attack, 
                            defense
                        FROM users 
                        WHERE character_name IS NOT NULL 
                        ORDER BY level DESC, exp DESC, coins DESC
                        LIMIT %s
                    ''', (limit,))
                    
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении топа игроков: {e}")
            return []
    
    def get_race_description(self, race):
        """Получить описание расы"""
        descriptions = {
            'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
            'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
            'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
            'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
        }
        return descriptions.get(race, "Неизвестная раса")
    
    def add_battle_history(self, user_id, monster_name, result, rounds, exp_gained, coins_gained, health_lost):
        """Добавить запись в историю боёв"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        INSERT INTO battle_history 
                        (user_id, monster_name, result, rounds, exp_gained, coins_gained, health_lost)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (user_id, monster_name, result, rounds, exp_gained, coins_gained, health_lost))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении истории боя: {e}")
            return False
    
    def backup_database(self):
        """Создать резервную копию базы данных"""
        try:
            # Эта функция будет вызываться извне для бэкапа
            # Для Railway лучше использовать встроенные инструменты бэкапа
            logger.info("✅ Для бэкапов используйте Railway Dashboard → PostgreSQL → Backups")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании бэкапа: {e}")
            return False
    def log_activity(self, user_id, action, details=""):
        """Логирование активности пользователя"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as (cursor, _):
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS activity_log (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            action VARCHAR(100),
                            details TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                        )
                    ''')
                    
                    cursor.execute('''
                        INSERT INTO activity_log (user_id, action, details)
                        VALUES (%s, %s, %s)
                    ''', (user_id, action, details))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка при логировании активности: {e}")
            return False
# Создаем глобальный экземпляр базы данных
db = PostgreSQLDatabase()
