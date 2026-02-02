import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

# Константы для database.py
RACES = {
    "human": {
        "name": "Человек",
        "strength": 10,
        "agility": 10,
        "intelligence": 10,
        "health": 100,
        "mana": 50,
        "racial_ability": "Адаптивность: +1 ко всем характеристикам"
    },
    "elf": {
        "name": "Эльф",
        "strength": 8,
        "agility": 14,
        "intelligence": 12,
        "health": 80,
        "mana": 100,
        "racial_ability": "Магический дар: +50% к мане, точные выстрелы"
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 14,
        "agility": 8,
        "intelligence": 9,
        "health": 120,
        "mana": 30,
        "racial_ability": "Каменная кожа: +20% к здоровью, сопротивление к магии"
    },
    "orc": {
        "name": "Орк",
        "strength": 16,
        "agility": 9,
        "intelligence": 6,
        "health": 110,
        "mana": 20,
        "racial_ability": "Ярость: двойной урон при низком здоровье"
    }
}

def get_connection():
    """Создание подключения к PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Для локальной разработки
        db_host = os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('PGPORT', '5432')
        db_name = os.getenv('PGDATABASE', 'railway')
        db_user = os.getenv('PGUSER', 'postgres')
        db_password = os.getenv('PGPASSWORD', '')
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения с sslmode=require: {e}")
        # Пробуем подключиться без sslmode
        try:
            conn = psycopg2.connect(database_url)
            return conn
        except Exception as e2:
            print(f"❌ Не удалось подключиться к БД: {e2}")
            return None

def init_db():
    """Инициализация таблиц в базе данных"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для инициализации")
            return
        
        cursor = conn.cursor()
        
        # Удаляем старую таблицу и создаем новую с правильной структурой
        cursor.execute("DROP TABLE IF EXISTS player_characters")
        
        # Создаем таблицу с полной структурой
        cursor.execute("""
            CREATE TABLE player_characters (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                character_name VARCHAR(100) NOT NULL,
                race VARCHAR(50) NOT NULL,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                strength INTEGER DEFAULT 10,
                agility INTEGER DEFAULT 10,
                intelligence INTEGER DEFAULT 10,
                health INTEGER DEFAULT 100,
                max_health INTEGER DEFAULT 100,
                mana INTEGER DEFAULT 50,
                max_mana INTEGER DEFAULT 50,
                gold INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                battle_wins INTEGER DEFAULT 0,
                battle_losses INTEGER DEFAULT 0
            )
        """)
        
        print("✅ Таблица 'player_characters' создана заново")
        
        # Создаем таблицу для логов боев
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                enemy_type VARCHAR(100),
                result VARCHAR(50),
                damage_dealt INTEGER DEFAULT 0,
                damage_taken INTEGER DEFAULT 0,
                gold_earned INTEGER DEFAULT 0,
                experience_earned INTEGER DEFAULT 0,
                battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу для инвентаря
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_inventory (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                item_type VARCHAR(50) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, item_type)
            )
        """)
        
        conn.commit()
        print("✅ База данных инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_character(user_id, username, character_name, race):
    """Создание нового персонажа"""
    conn = None
    cursor = None
    try:
        # Проверяем, что раса существует
        if race not in RACES:
            return False, "Неизвестная раса"
        
        race_data = RACES[race]
        
        conn = get_connection()
        if not conn:
            return False, "Не удалось подключиться к базе данных"
        
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже персонаж у пользователя
        cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            return False, "У вас уже есть персонаж!"
        
        # Создаем персонажа с характеристиками расы
        cursor.execute("""
            INSERT INTO player_characters 
            (user_id, character_name, race, level, experience,
             strength, agility, intelligence, health, max_health, 
             mana, max_mana, gold)
            VALUES (%s, %s, %s, 1, 0, %s, %s, %s, %s, %s, %s, %s, 100)
        """, (
            user_id, character_name, race,
            race_data['strength'], race_data['agility'], race_data['intelligence'],
            race_data['health'], race_data['health'],
            race_data['mana'], race_data['mana']
        ))
        
        conn.commit()
        print(f"✅ Персонаж создан для user_id: {user_id}")
        return True, "Персонаж успешно создан!"
        
    except Exception as e:
        print(f"❌ Ошибка при создании персонажа: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка при создании персонажа: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_character(user_id):
    """Получение информации о персонаже"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для получения персонажа")
            return None
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM player_characters 
            WHERE user_id = %s
        """, (user_id,))
        
        character = cursor.fetchone()
        
        if character:
            # Проверяем и применяем регенерацию
            character = apply_regeneration(character)
            
            # Обновляем время последней активности
            cursor.execute("""
                UPDATE player_characters 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()
        
        return character
        
    except Exception as e:
        print(f"❌ Ошибка при получении персонажа: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def apply_regeneration(character):
    """Применение регенерации здоровья и маны"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return character
        
        cursor = conn.cursor()
        
        # Проверяем, прошло ли достаточно времени с последней регенерации
        last_regeneration = character.get('last_regeneration')
        current_time = datetime.now()
        
        if last_regeneration:
            # Преобразуем строку в datetime, если нужно
            if isinstance(last_regeneration, str):
                last_regeneration = datetime.fromisoformat(last_regeneration.replace('Z', '+00:00'))
            
            time_diff = current_time - last_regeneration
            
            # Регенерация каждые 5 минут (300 секунд)
            if time_diff.total_seconds() >= 300:
                # Рассчитываем регенерацию
                health_regen = character['max_health'] * 0.05  # 5% от макс. здоровья
                mana_regen = character['max_mana'] * 0.10  # 10% от макс. маны
                
                new_health = min(character['max_health'], character['health'] + int(health_regen))
                new_mana = min(character['max_mana'], character['mana'] + int(mana_regen))
                
                # Обновляем в базе данных
                cursor.execute("""
                    UPDATE player_characters 
                    SET health = %s, mana = %s, last_regeneration = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING health, mana
                """, (new_health, new_mana, character['user_id']))
                
                result = cursor.fetchone()
                conn.commit()
                
                if result:
                    character['health'] = result[0]
                    character['mana'] = result[1]
                    character['last_regeneration'] = current_time
        
        return character
        
    except Exception as e:
        print(f"❌ Ошибка при регенерации: {e}")
        return character
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_races():
    """Получение списка всех рас"""
    return RACES

def update_character_stats(user_id, **kwargs):
    """Обновление характеристик персонажа"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        values.append(user_id)
        query = f"UPDATE player_characters SET {', '.join(set_clauses)} WHERE user_id = %s"
        
        cursor.execute(query, values)
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении персонажа: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_experience(user_id, exp_amount):
    """Добавление опыта персонажу"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, False, 0
        
        cursor = conn.cursor()
        
        # Получаем текущий опыт и уровень
        cursor.execute("SELECT experience, level FROM player_characters WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, False, 0
        
        current_exp, current_level = result
        new_exp = current_exp + exp_amount
        
        # Проверка повышения уровня (каждые 100 опыта)
        new_level = current_level
        level_up = False
        
        # Если опыт превысил порог для текущего уровня
        exp_needed = current_level * 100
        if new_exp >= exp_needed:
            new_level = current_level + 1
            level_up = True
            
            # Увеличиваем характеристики при повышении уровня
            cursor.execute("""
                UPDATE player_characters 
                SET experience = %s, level = %s,
                    strength = strength + 2,
                    agility = agility + 2,
                    intelligence = intelligence + 2,
                    max_health = max_health + 20,
                    max_mana = max_mana + 10,
                    health = max_health + 20,  # Восстанавливаем здоровье
                    mana = max_mana + 10       # Восстанавливаем ману
                WHERE user_id = %s
            """, (new_exp, new_level, user_id))
        else:
            cursor.execute("""
                UPDATE player_characters 
                SET experience = %s
                WHERE user_id = %s
            """, (new_exp, user_id))
        
        conn.commit()
        return True, level_up, new_level
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении опыта: {e}")
        if conn:
            conn.rollback()
        return False, False, 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_gold(user_id, gold_amount):
    """Добавление золота персонажу"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE player_characters 
            SET gold = gold + %s 
            WHERE user_id = %s
        """, (gold_amount, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка при добавлении золота: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def buy_item(user_id, item_type, item_name, price, effect_amount=None):
    """Покупка предмета в магазине"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, "Ошибка подключения к БД"
        
        cursor = conn.cursor()
        
        # Проверяем баланс игрока
        cursor.execute("SELECT gold FROM player_characters WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, "Персонаж не найден"
        
        current_gold = result[0]
        
        if current_gold < price:
            return False, f"Недостаточно золота! Нужно {price}, есть {current_gold}"
        
        # Списываем золото
        cursor.execute("""
            UPDATE player_characters 
            SET gold = gold - %s 
            WHERE user_id = %s
        """, (price, user_id))
        
        # Применяем эффект предмета, если это зелье
        if item_type == 'potion':
            if 'health' in item_name.lower():
                # Лечебное зелье
                cursor.execute("""
                    UPDATE player_characters 
                    SET health = LEAST(max_health, health + %s)
                    WHERE user_id = %s
                """, (effect_amount, user_id))
            elif 'mana' in item_name.lower():
                # Зелье маны
                cursor.execute("""
                    UPDATE player_characters 
                    SET mana = LEAST(max_mana, mana + %s)
                    WHERE user_id = %s
                """, (effect_amount, user_id))
        
        # Добавляем в инвентарь
        cursor.execute("""
            INSERT INTO player_inventory (user_id, item_type, item_name, quantity)
            VALUES (%s, %s, %s, 1)
            ON CONFLICT (user_id, item_type) 
            DO UPDATE SET quantity = player_inventory.quantity + 1
        """, (user_id, item_type, item_name))
        
        conn.commit()
        return True, f"Предмет '{item_name}' куплен успешно!"
        
    except Exception as e:
        print(f"❌ Ошибка при покупке предмета: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка при покупке: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_inventory(user_id):
    """Получение инвентаря игрока"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT item_type, item_name, quantity 
            FROM player_inventory 
            WHERE user_id = %s
            ORDER BY item_type
        """, (user_id,))
        
        return cursor.fetchall()
        
    except Exception as e:
        print(f"❌ Ошибка при получении инвентаря: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def log_battle(user_id, enemy_type, result, damage_dealt=0, damage_taken=0, gold_earned=0, experience_earned=0):
    """Логирование боя"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица battle_logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                enemy_type VARCHAR(100),
                result VARCHAR(50),
                damage_dealt INTEGER DEFAULT 0,
                damage_taken INTEGER DEFAULT 0,
                gold_earned INTEGER DEFAULT 0,
                experience_earned INTEGER DEFAULT 0,
                battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO battle_logs 
            (user_id, enemy_type, result, damage_dealt, damage_taken, gold_earned, experience_earned)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, enemy_type, result, damage_dealt, damage_taken, gold_earned, experience_earned))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка при логировании боя: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_player_stats(user_id):
    """Получение статистики игрока"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                character_name,
                race,
                level,
                experience,
                battle_wins,
                battle_losses,
                gold,
                created_at
            FROM player_characters 
            WHERE user_id = %s
        """, (user_id,))
        
        return cursor.fetchone()
        
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
