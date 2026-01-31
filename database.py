import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    def __init__(self):
        # Получаем URL базы данных из переменных окружения Railway
        self.database_url = os.environ.get('DATABASE_URL')
        
        # На Railway проверьте также другие возможные имена переменных
        if not self.database_url:
            self.database_url = os.environ.get('POSTGRESQL_URL')
        
        if not self.database_url:
            # Проверяем, не запущено ли локально
            if os.environ.get('RAILWAY_ENVIRONMENT'):
                # На Railway, но DATABASE_URL не установлен
                logger.error("❌ ОШИБКА: DATABASE_URL не установлена на Railway!")
                logger.error("   Добавьте переменную DATABASE_URL в разделе Variables")
                logger.error("   Или создайте PostgreSQL базу через New -> Database")
                # Создаем заглушку, чтобы бот мог работать без БД
                self.database_url = None
                return
            else:
                # Локальная разработка
                logger.warning("⚠️  DATABASE_URL не установлена, работаем без БД")
                self.database_url = None
                return
        
        # Исправляем формат URL для psycopg2
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info(f"✅ DATABASE_URL обнаружена")
        
        # Пытаемся подключиться
        self.retry_connection()
    
    def retry_connection(self):
        """Повторные попытки подключения к БД"""
        if not self.database_url:
            logger.error("❌ Нет DATABASE_URL для подключения")
            return False
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.init_db()
                logger.info(f"✅ База данных успешно инициализирована")
                return True
            except Exception as e:
                logger.error(f"❌ Попытка {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ Не удалось подключиться к базе данных")
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
    
    def get_user(self, user_id):
        """Получить пользователя"""
        if not self.database_url:
            return None
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                    result = cursor.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        """Создать пользователя"""
        if not self.database_url:
            return False
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO users (user_id, username, first_name, last_name, exp_to_next_level)
                        VALUES (%s, %s, %s, %s, 100)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            last_active = CURRENT_TIMESTAMP
                    ''', (user_id, username, first_name, last_name))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя {user_id}: {e}")
            return False
    
    def update_user(self, user_id, **kwargs):
        """Обновить данные пользователя"""
        if not self.database_url or not kwargs:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
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
            logger.error(f"❌ Ошибка обновления пользователя {user_id}: {e}")
            return False
    
    def complete_character_creation(self, user_id, character_name, race):
        """Завершить создание персонажа"""
        if not self.database_url:
            return False
            
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
            logger.error(f"❌ Ошибка создания персонажа: {e}")
            return False
    
    def add_exp(self, user_id, exp_amount):
        """Добавить опыт"""
        if not self.database_url:
            return False
            
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            skill_points_gained = 0
            
            while new_exp >= user['exp_to_next_level']:
                new_exp -= user['exp_to_next_level']
                new_level += 1
                skill_points_gained += 1
                exp_to_next = int(100 * (1.5 ** (new_level - 1)))
                
                self.update_user(
                    user_id,
                    level=new_level,
                    exp=new_exp,
                    exp_to_next_level=exp_to_next,
                    skill_points=user['skill_points'] + skill_points_gained
                )
                user = self.get_user(user_id)
            
            if exp_amount > 0 and skill_points_gained == 0:
                return self.update_user(user_id, exp=new_exp)
            
            return skill_points_gained > 0
        except Exception as e:
            logger.error(f"❌ Ошибка добавления опыта: {e}")
            return False
    
    def add_coins(self, user_id, coins_amount):
        """Добавить монеты"""
        if not self.database_url:
            return False
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE users 
                        SET coins = GREATEST(0, coins + %s)
                        WHERE user_id = %s
                    ''', (coins_amount, user_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Ошибка добавления монет: {e}")
            return False
    
    def can_hunt_today(self, user_id):
        """Проверить лимит охоты"""
        if not self.database_url:
            return False, 0, 5
            
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0, 5
            
            today = datetime.now().date()
            last_hunt_date = user['last_hunt_date']
            
            if not last_hunt_date or last_hunt_date != today:
                self.update_user(user_id, daily_hunts=0, last_hunt_date=today)
                return True, 0, 5
            
            return user['daily_hunts'] < 5, user['daily_hunts'], 5
        except Exception as e:
            logger.error(f"❌ Ошибка проверки охоты: {e}")
            return False, 0, 5
    
    def increment_daily_hunts(self, user_id):
        """Увеличить счетчик охот"""
        if not self.database_url:
            return False
            
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
            logger.error(f"❌ Ошибка увеличения счетчика охот: {e}")
            return False
    
    def use_skill_point(self, user_id, stat):
        """Использовать очко навыка"""
        if not self.database_url:
            return False
            
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
            logger.error(f"❌ Ошибка использования очка навыка: {e}")
            return False
    
    def add_to_inventory(self, user_id, item_type, item_name, quantity=1):
        """Добавить предмет в инвентарь"""
        if not self.database_url:
            return False
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO inventory (user_id, item_type, item_name, quantity)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (user_id, item_type, item_name) 
                        DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity
                    ''', (user_id, item_type, item_name, quantity))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в инвентарь: {e}")
            return False
    
    def get_inventory(self, user_id):
        """Получить инвентарь"""
        if not self.database_url:
            return []
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT item_type, item_name, quantity 
                        FROM inventory 
                        WHERE user_id = %s AND quantity > 0
                        ORDER BY item_type, item_name
                    ''', (user_id,))
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Ошибка получения инвентаря: {e}")
            return []
    
    def use_item(self, user_id, item_type, item_name):
        """Использовать предмет"""
        if not self.database_url:
            return False
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Проверяем наличие
                    cursor.execute('''
                        SELECT id, quantity FROM inventory 
                        WHERE user_id = %s AND item_type = %s AND item_name = %s
                    ''', (user_id, item_type, item_name))
                    
                    item = cursor.fetchone()
                    if not item or item['quantity'] < 1:
                        return False
                    
                    # Удаляем или уменьшаем количество
                    if item['quantity'] == 1:
                        cursor.execute('DELETE FROM inventory WHERE id = %s', (item['id'],))
                    else:
                        cursor.execute('''
                            UPDATE inventory SET quantity = quantity - 1 
                            WHERE id = %s
                        ''', (item['id'],))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка использования предмета: {e}")
            return False
    
    def get_race_description(self, race):
        """Описание расы"""
        descriptions = {
            'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
            'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
            'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
            'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
        }
        return descriptions.get(race, "Неизвестная раса")
    
    def get_top_players(self, limit=5):
        """Топ игроков"""
        if not self.database_url:
            return []
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT character_name, race, level, exp, coins, attack, defense
                        FROM users 
                        WHERE character_name IS NOT NULL 
                        ORDER BY level DESC, exp DESC, coins DESC
                        LIMIT %s
                    ''', (limit,))
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Ошибка получения топа игроков: {e}")
            return []

# Создаем глобальный экземпляр базы данных
db = PostgreSQLDatabase()
