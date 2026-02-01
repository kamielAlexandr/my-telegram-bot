# database_postgres.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import logging

logger = logging.getLogger(__name__)

class PostgresDatabase:
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        if not self.connection_string:
            # Для локальной разработки
            self.connection_string = os.environ.get('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/game_bot')
        
        logger.info(f"🔗 Подключение к PostgreSQL: {self.connection_string[:30]}...")
        self.init_db()
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        conn = psycopg2.connect(self.connection_string)
        return conn
    
    def init_db(self):
        """Инициализация таблиц в PostgreSQL"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
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
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    item_type TEXT,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1
                )
            ''')
            
            # Таблица для статистики (опционально)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_stats (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT,
                    user_id BIGINT,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cursor.close()
            logger.info("✅ PostgreSQL база данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_user(self, user_id):
        """Получить пользователя по ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return dict(user) if user else None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        """Создать нового пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            cursor.close()
            logger.info(f"👤 Создан/обновлен пользователь: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def update_user(self, user_id, **kwargs):
        """Обновить данные пользователя"""
        try:
            if not kwargs:
                return False
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{key} = %s" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)
            
            query = f'''
                UPDATE users 
                SET {set_clause}, last_active = CURRENT_TIMESTAMP
                WHERE user_id = %s
            '''
            
            cursor.execute(query, values)
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            
            return affected > 0
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
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
            return self.update_user(user_id, character_name=character_name, race=race)
        except Exception as e:
            logger.error(f"❌ Ошибка при создании персонажа: {e}")
            return False
    
    def add_exp(self, user_id, exp_amount):
        """Добавить опыт пользователю"""
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
            logger.error(f"❌ Ошибка при добавлении опыта: {e}")
            return False
    
    def add_coins(self, user_id, coins_amount):
        """Добавить/убрать монеты"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_coins = max(0, user['coins'] + coins_amount)
            return self.update_user(user_id, coins=new_coins)
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении монет: {e}")
            return False
    
    def can_hunt_today(self, user_id):
        """Проверить, может ли пользователь охотиться сегодня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0, 5
            
            today = datetime.date.today()
            last_hunt_date = user['last_hunt_date']
            
            if isinstance(last_hunt_date, str):
                last_hunt_date = datetime.datetime.strptime(last_hunt_date, '%Y-%m-%d').date()
            
            if last_hunt_date != today:
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
            
            today = datetime.date.today()
            last_hunt_date = user['last_hunt_date']
            
            if isinstance(last_hunt_date, str):
                last_hunt_date = datetime.datetime.strptime(last_hunt_date, '%Y-%m-%d').date()
            
            if last_hunt_date != today:
                return self.update_user(user_id, daily_hunts=1, last_hunt_date=today)
            
            return self.update_user(user_id, daily_hunts=user['daily_hunts'] + 1)
        except Exception as e:
            logger.error(f"❌ Ошибка при увеличении счетчика охот: {e}")
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
                'health': {'max_health': user['max_health'] + 15, 'health': min(user['health'] + 15, user['max_health'] + 15)}
            }
            
            if stat not in improvements:
                return False
            
            improvement = improvements[stat]
            improvement['skill_points'] = user['skill_points'] - 1
            
            return self.update_user(user_id, **improvement)
        except Exception as e:
            logger.error(f"❌ Ошибка при использовании очка навыка: {e}")
            return False
    
    def add_to_inventory(self, user_id, item_type, item_name, quantity=1):
        """Добавить предмет в инвентарь"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity FROM inventory 
                WHERE user_id = %s AND item_type = %s AND item_name = %s
            ''', (user_id, item_type, item_name))
            
            existing = cursor.fetchone()
            
            if existing:
                new_quantity = existing[1] + quantity
                cursor.execute('''
                    UPDATE inventory SET quantity = %s 
                    WHERE id = %s
                ''', (new_quantity, existing[0]))
            else:
                cursor.execute('''
                    INSERT INTO inventory (user_id, item_type, item_name, quantity)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, item_type, item_name, quantity))
            
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении в инвентарь: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_inventory(self, user_id):
        """Получить инвентарь пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT item_type, item_name, quantity 
                FROM inventory 
                WHERE user_id = %s AND quantity > 0
                ORDER BY item_type, item_name
            ''', (user_id,))
            
            items = cursor.fetchall()
            cursor.close()
            return [dict(item) for item in items]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении инвентаря: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def use_item(self, user_id, item_type, item_name):
        """Использовать предмет из инвентаря"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity FROM inventory 
                WHERE user_id = %s AND item_type = %s AND item_name = %s
            ''', (user_id, item_type, item_name))
            
            item = cursor.fetchone()
            if not item or item[1] < 1:
                return False
            
            if item[1] == 1:
                cursor.execute('DELETE FROM inventory WHERE id = %s', (item[0],))
            else:
                cursor.execute('''
                    UPDATE inventory SET quantity = quantity - 1 
                    WHERE id = %s
                ''', (item[0],))
            
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при использовании предмета: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_top_players(self, limit=5):
        """Получить топ игроков"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT character_name, race, level, exp, coins, attack, defense
                FROM users 
                WHERE character_name IS NOT NULL 
                ORDER BY level DESC, exp DESC, coins DESC
                LIMIT %s
            ''', (limit,))
            
            top_players = cursor.fetchall()
            cursor.close()
            return [dict(player) for player in top_players]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении топа игроков: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_race_description(self, race):
        """Получить описание расы"""
        descriptions = {
            'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
            'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
            'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
            'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
        }
        return descriptions.get(race, "Неизвестная раса")
