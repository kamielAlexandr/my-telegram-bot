import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

# Константы для database.py - УСЛОЖНЕННЫЕ ЗНАЧЕНИЯ
RACES = {
    "human": {
        "name": "Человек",
        "strength": 8,
        "agility": 8,
        "intelligence": 8,
        "health": 80,
        "mana": 30,
        "racial_ability": "Адаптивность: +5% ко всем характеристикам на 1 ход"
    },
    "elf": {
        "name": "Эльф",
        "strength": 6,
        "agility": 12,
        "intelligence": 10,
        "health": 65,
        "mana": 60,
        "racial_ability": "Магический дар: +30% к мане, точные выстрелы"
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 11,
        "agility": 5,
        "intelligence": 7,
        "health": 100,
        "mana": 20,
        "racial_ability": "Каменная кожа: +15% к здоровью, сопротивление к магии"
    },
    "orc": {
        "name": "Орк",
        "strength": 13,
        "agility": 7,
        "intelligence": 5,
        "health": 90,
        "mana": 15,
        "racial_ability": "Ярость: +50% урон при низком здоровье"
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
    """Инициализация таблиц в базе данных - ПЕРЕДЕЛАННАЯ ВЕРСИЯ"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для инициализации")
            return
        
        cursor = conn.cursor()
        
        # Создаем таблицу, если она не существует
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_characters (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                character_name VARCHAR(100) NOT NULL,
                race VARCHAR(50) NOT NULL,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                rank VARCHAR(10) DEFAULT 'E',
                strength INTEGER DEFAULT 10,
                agility INTEGER DEFAULT 10,
                intelligence INTEGER DEFAULT 10,
                health INTEGER DEFAULT 100,
                max_health INTEGER DEFAULT 100,
                mana INTEGER DEFAULT 50,
                max_mana INTEGER DEFAULT 50,
                gold INTEGER DEFAULT 100,
                stat_points INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                battle_wins INTEGER DEFAULT 0,
                battle_losses INTEGER DEFAULT 0,
                boss_kills INTEGER DEFAULT 0,
                mini_boss_kills INTEGER DEFAULT 0
            )
        """)
        
        # Проверяем и добавляем недостающие столбцы
        columns_to_check = [
            ('rank', "VARCHAR(10) DEFAULT 'E'"),
            ('last_active', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('last_regeneration', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('boss_kills', 'INTEGER DEFAULT 0'),
            ('mini_boss_kills', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_type in columns_to_check:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='player_characters' AND column_name=%s
            """, (column_name,))
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE player_characters ADD COLUMN {column_name} {column_type}")
                print(f"✅ Столбец '{column_name}' добавлен в таблицу 'player_characters'")
        
        print("✅ Таблица 'player_characters' создана/обновлена")
        
        # Создаем таблицу для логов боев
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                enemy_type VARCHAR(100),
                enemy_name VARCHAR(100),
                result VARCHAR(50),
                damage_dealt INTEGER DEFAULT 0,
                damage_taken INTEGER DEFAULT 0,
                gold_earned INTEGER DEFAULT 0,
                experience_earned INTEGER DEFAULT 0,
                is_boss BOOLEAN DEFAULT FALSE,
                is_mini_boss BOOLEAN DEFAULT FALSE,
                battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # УДАЛЯЕМ СТАРУЮ ТАБЛИЦУ ИНВЕНТАРЯ, ЕСЛИ ОНА СУЩЕСТВУЕТ
        cursor.execute("DROP TABLE IF EXISTS player_inventory CASCADE")
        print("🗑️ Старая таблица инвентаря удалена")
        
        # СОЗДАЕМ НОВУЮ ТАБЛИЦУ ИНВЕНТАРЯ
        cursor.execute("""
            CREATE TABLE player_inventory (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                item_key VARCHAR(100) NOT NULL,
                item_type VARCHAR(50) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                quantity INTEGER DEFAULT 1,
                effect_amount INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем индексы для быстрого поиска
        cursor.execute("""
            CREATE INDEX idx_player_inventory_user_item 
            ON player_inventory (user_id, item_key)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_player_inventory_user 
            ON player_inventory (user_id)
        """)
        
        conn.commit()
        print("✅ База данных полностью пересоздана и инициализирована")
        print("✅ Таблица 'player_inventory' создана")
        
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
    """Создание нового персонажа - УСЛОЖНЕННАЯ ВЕРСИЯ"""
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
            (user_id, character_name, race, level, experience, rank,
             strength, agility, intelligence, health, max_health, 
             mana, max_mana, gold, stat_points)
            VALUES (%s, %s, %s, 1, 0, 'E', %s, %s, %s, %s, %s, %s, %s, 50, 2)
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
            
            # Если ранг не установлен, рассчитываем его
            if not character.get('rank'):
                rank = calculate_rank(character['level'], character['experience'])
                cursor.execute("""
                    UPDATE player_characters 
                    SET rank = %s
                    WHERE user_id = %s
                """, (rank, user_id))
                character['rank'] = rank
            
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
                try:
                    last_regeneration = datetime.fromisoformat(last_regeneration.replace('Z', '+00:00'))
                except:
                    try:
                        last_regeneration = datetime.strptime(last_regeneration, '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        last_regeneration = None
            
            if last_regeneration:
                time_diff = current_time - last_regeneration
                
                # Регенерация каждые 10 минут (600 секунд)
                if time_diff.total_seconds() >= 600:
                    # Рассчитываем сколько интервалов прошло
                    intervals_passed = int(time_diff.total_seconds() // 600)
                    
                    # Регенерация за каждый интервал
                    health_per_interval = character['max_health'] * 0.03  # 3% от макс. здоровья
                    mana_per_interval = character['max_mana'] * 0.05  # 5% от макс. маны
                    
                    total_health_regen = int(health_per_interval * intervals_passed)
                    total_mana_regen = int(mana_per_interval * intervals_passed)
                    
                    new_health = min(character['max_health'], character['health'] + total_health_regen)
                    new_mana = min(character['max_mana'], character['mana'] + total_mana_regen)
                    
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

def calculate_rank(level, experience):
    """Определение ранга на основе уровня и опыта - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    if level >= 50:  # Повышены требования
        return 'S'
    elif level >= 40:
        return 'A'
    elif level >= 30:
        return 'B'
    elif level >= 20:
        return 'C'
    elif level >= 10:
        return 'D'
    else:
        return 'E'

def add_experience(user_id, exp_amount):
    """Добавление опыта персонажу - УСЛОЖНЕННАЯ ВЕРСИЯ"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, False, 0, 0
        
        cursor = conn.cursor()
        
        # Получаем текущие данные персонажа
        cursor.execute("""
            SELECT experience, level, stat_points, rank 
            FROM player_characters WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, False, 0, 0
        
        current_exp, current_level, current_stat_points, current_rank = result
        new_exp = current_exp + exp_amount
        
        # УСЛОЖНЕННАЯ ПРОВЕРКА ПОВЫШЕНИЯ УРОВНЯ
        new_level = current_level
        level_up = False
        stat_points_gained = 0
        
        # Проверяем, достаточно ли опыта для повышения уровня
        # Формула: для перехода с уровня N на N+1 нужно N * 150 опыта
        exp_needed = current_level * 150
        
        # Можно получить несколько уровней сразу, если много опыта
        while True:
            # Общий опыт для уровня L: сумма от 1 до L (i * 150)
            total_exp_for_next_level = ((new_level) * (new_level + 1) * 150) // 2
            
            if new_exp >= total_exp_for_next_level:
                new_level += 1
                level_up = True
                stat_points_gained += 2  # Даем только 2 очка характеристик за уровень
            else:
                break
        
        if level_up:
            # Рассчитываем новый ранг
            new_rank = calculate_rank(new_level, new_exp)
            
            # Рассчитываем увеличение здоровья и маны (5 HP и 3 MP за уровень)
            health_increase = 5 * (new_level - current_level)
            mana_increase = 3 * (new_level - current_level)
            
            # Обновляем персонажа
            cursor.execute("""
                UPDATE player_characters 
                SET experience = %s, level = %s, stat_points = stat_points + %s, rank = %s,
                    max_health = max_health + %s,
                    max_mana = max_mana + %s,
                    health = max_health + %s,  # Восстанавливаем здоровье до нового максимума
                    mana = max_mana + %s       # Восстанавливаем ману до нового максимума
                WHERE user_id = %s
            """, (new_exp, new_level, stat_points_gained, new_rank, 
                  health_increase, mana_increase, health_increase, mana_increase, 
                  user_id))
        else:
            # Обновляем только опыт
            cursor.execute("""
                UPDATE player_characters 
                SET experience = %s
                WHERE user_id = %s
            """, (new_exp, user_id))
        
        conn.commit()
        return True, level_up, new_level, stat_points_gained
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении опыта: {e}")
        if conn:
            conn.rollback()
        return False, False, 0, 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_stat_point(user_id, stat_type):
    """Распределение очка характеристики"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, "Ошибка подключения к БД"
        
        cursor = conn.cursor()
        
        # Проверяем, есть ли очки характеристик
        cursor.execute("SELECT stat_points FROM player_characters WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, "Персонаж не найден"
        
        stat_points = result[0]
        
        if stat_points <= 0:
            return False, "У тебя нет очков характеристик для распределения!"
        
        # Определяем, какую характеристику улучшаем
        if stat_type == 'strength':
            cursor.execute("""
                UPDATE player_characters 
                SET strength = strength + 1, stat_points = stat_points - 1
                WHERE user_id = %s
            """, (user_id,))
            
        elif stat_type == 'agility':
            cursor.execute("""
                UPDATE player_characters 
                SET agility = agility + 1, stat_points = stat_points - 1
                WHERE user_id = %s
            """, (user_id,))
            
        elif stat_type == 'intelligence':
            # При повышении интеллекта также увеличиваем максимальную ману
            cursor.execute("""
                UPDATE player_characters 
                SET intelligence = intelligence + 1, 
                    stat_points = stat_points - 1,
                    max_mana = max_mana + 3,
                    mana = mana + 3
                WHERE user_id = %s
            """, (user_id,))
            
        else:
            return False, "Неизвестная характеристика"
        
        conn.commit()
        return True, f"Характеристика '{stat_type}' увеличена на 1!"
        
    except Exception as e:
        print(f"❌ Ошибка при распределении характеристики: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка: {e}"
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

def increment_battle_stats(user_id, won=True, is_boss=False, is_mini_boss=False):
    """Увеличение счетчика побед/поражений и убийств боссов"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        if won:
            if is_boss:
                cursor.execute("""
                    UPDATE player_characters 
                    SET battle_wins = battle_wins + 1,
                        boss_kills = boss_kills + 1
                    WHERE user_id = %s
                """, (user_id,))
            elif is_mini_boss:
                cursor.execute("""
                    UPDATE player_characters 
                    SET battle_wins = battle_wins + 1,
                        mini_boss_kills = mini_boss_kills + 1
                    WHERE user_id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    UPDATE player_characters 
                    SET battle_wins = battle_wins + 1
                    WHERE user_id = %s
                """, (user_id,))
        else:
            cursor.execute("""
                UPDATE player_characters 
                SET battle_losses = battle_losses + 1
                WHERE user_id = %s
            """, (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка при обновлении статистики боя: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=None):
    """Покупка предмета в магазине - ПРОСТАЯ РАБОЧАЯ ВЕРСИЯ"""
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
        
        # Устанавливаем effect_amount по умолчанию, если не передан
        if effect_amount is None:
            if 'small_health_potion' in item_key:
                effect_amount = 20
            elif 'large_health_potion' in item_key:
                effect_amount = 40
            elif 'small_mana_potion' in item_key:
                effect_amount = 15
            elif 'large_mana_potion' in item_key:
                effect_amount = 30
            else:
                effect_amount = 0
        
        # ПРОСТО ВСТАВЛЯЕМ НОВУЮ ЗАПИСЬ
        cursor.execute("""
            INSERT INTO player_inventory 
            (user_id, item_key, item_type, item_name, quantity, effect_amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, item_key, item_type, item_name, 1, effect_amount))
        
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
    """Получение инвентаря игрока - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Группируем предметы по item_key и суммируем количество
        cursor.execute("""
            SELECT 
                item_key,
                item_type,
                item_name,
                SUM(quantity) as quantity,
                MAX(effect_amount) as effect_amount
            FROM player_inventory 
            WHERE user_id = %s AND quantity > 0
            GROUP BY item_key, item_type, item_name
            ORDER BY 
                CASE item_type
                    WHEN 'potion' THEN 1
                    WHEN 'weapon' THEN 2
                    WHEN 'armor' THEN 3
                    WHEN 'artifact' THEN 4
                    ELSE 5
                END,
                item_name
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

def use_item(user_id, item_key, item_type, item_name, effect_amount):
    """Использование предмета из инвентаря"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, "Ошибка подключения к БД"
        
        cursor = conn.cursor()
        
        # Находим первую запись с этим предметом
        cursor.execute("""
            SELECT id, quantity, effect_amount FROM player_inventory 
            WHERE user_id = %s AND item_key = %s AND quantity > 0
            ORDER BY id
            LIMIT 1
        """, (user_id, item_key))
        
        result = cursor.fetchone()
        if not result:
            return False, "Предмет не найден в инвентаре"
        
        item_id, quantity, db_effect_amount = result
        
        # Используем effect_amount из базы, если он не передан
        if effect_amount is None or effect_amount == 0:
            effect_amount = db_effect_amount or 0
        
        # Уменьшаем количество на 1
        new_quantity = quantity - 1
        
        if new_quantity <= 0:
            # Удаляем запись, если предметы закончились
            cursor.execute("""
                DELETE FROM player_inventory 
                WHERE id = %s
            """, (item_id,))
        else:
            # Обновляем количество
            cursor.execute("""
                UPDATE player_inventory 
                SET quantity = %s
                WHERE id = %s
            """, (new_quantity, item_id))
        
        # ВОССТАНАВЛИВАЕМ ЗДОРОВЬЕ ИЛИ МАНУ
        message = ""
        
        if 'health_potion' in item_key:
            # Зелье здоровья - получаем текущее состояние персонажа
            cursor.execute("""
                SELECT health, max_health FROM player_characters 
                WHERE user_id = %s
            """, (user_id,))
            char_result = cursor.fetchone()
            
            if not char_result:
                conn.rollback()
                return False, "Персонаж не найден"
            
            current_health, max_health = char_result
            new_health = min(max_health, current_health + effect_amount)
            health_restored = new_health - current_health
            
            # Обновляем здоровье
            cursor.execute("""
                UPDATE player_characters 
                SET health = %s
                WHERE user_id = %s
            """, (new_health, user_id))
            
            message = f"Использовано {item_name}. Восстановлено {health_restored} HP!"
            
        elif 'mana_potion' in item_key:
            # Зелье маны - получаем текущее состояние персонажа
            cursor.execute("""
                SELECT mana, max_mana FROM player_characters 
                WHERE user_id = %s
            """, (user_id,))
            char_result = cursor.fetchone()
            
            if not char_result:
                conn.rollback()
                return False, "Персонаж не найден"
            
            current_mana, max_mana = char_result
            new_mana = min(max_mana, current_mana + effect_amount)
            mana_restored = new_mana - current_mana
            
            # Обновляем ману
            cursor.execute("""
                UPDATE player_characters 
                SET mana = %s
                WHERE user_id = %s
            """, (new_mana, user_id))
            
            message = f"Использовано {item_name}. Восстановлено {mana_restored} MP!"
        else:
            # Для других типов предметов
            message = f"Предмет '{item_name}' использован!"
        
        conn.commit()
        return True, message
        
    except Exception as e:
        print(f"❌ Ошибка при использовании предмета: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def log_battle(user_id, enemy_type, enemy_name, result, damage_dealt=0, damage_taken=0, 
               gold_earned=0, experience_earned=0, is_boss=False, is_mini_boss=False):
    """Логирование боя"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO battle_logs 
            (user_id, enemy_type, enemy_name, result, damage_dealt, damage_taken, 
             gold_earned, experience_earned, is_boss, is_mini_boss)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, enemy_type, enemy_name, result, damage_dealt, damage_taken, 
              gold_earned, experience_earned, is_boss, is_mini_boss))
        
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
                rank,
                experience,
                stat_points,
                battle_wins,
                battle_losses,
                boss_kills,
                mini_boss_kills,
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

def get_top_players(limit=10):
    """Получение топ-N игроков по уровню и опыту"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                character_name,
                race,
                level,
                rank,
                experience,
                battle_wins,
                battle_losses,
                boss_kills,
                mini_boss_kills,
                gold,
                created_at
            FROM player_characters 
            ORDER BY level DESC, experience DESC, boss_kills DESC, battle_wins DESC
            LIMIT %s
        """, (limit,))
        
        return cursor.fetchall()
        
    except Exception as e:
        print(f"❌ Ошибка при получении топа игроков: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
