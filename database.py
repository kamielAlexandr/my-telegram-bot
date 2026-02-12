import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

# Константы (оставил как есть)
RACES = {
    "human": {
        "name": "Человек",
        "strength": 8, "agility": 8, "intelligence": 8, "vitality": 8,
        "health_multiplier": 8, "mana_multiplier": 3,
        "racial_ability": "Адаптивность: +5% ко всем характеристикам на 1 ход"
    },
    "elf": {
        "name": "Эльф",
        "strength": 6, "agility": 12, "intelligence": 10, "vitality": 6,
        "health_multiplier": 6, "mana_multiplier": 6,
        "racial_ability": "Магический дар: +30% к мане, точные выстрелы"
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 11, "agility": 5, "intelligence": 7, "vitality": 10,
        "health_multiplier": 10, "mana_multiplier": 2,
        "racial_ability": "Каменная кожа: +15% к здоровью, сопротивление к магии"
    },
    "orc": {
        "name": "Орк",
        "strength": 13, "agility": 7, "intelligence": 5, "vitality": 9,
        "health_multiplier": 9, "mana_multiplier": 1.5,
        "racial_ability": "Ярость: +50% урон при низком здоровье"
    }
}

def get_connection():
    """Создание подключения к PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url: return None
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except:
        try:
            conn = psycopg2.connect(database_url)
            return conn
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            return None

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            # Таблица персонажей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_characters (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    character_name VARCHAR(100) NOT NULL,
                    race VARCHAR(50) NOT NULL,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    rank VARCHAR(10) DEFAULT 'E',
                    strength INTEGER DEFAULT 8,
                    agility INTEGER DEFAULT 8,
                    intelligence INTEGER DEFAULT 8,
                    vitality INTEGER DEFAULT 8,
                    health INTEGER DEFAULT 64,
                    max_health INTEGER DEFAULT 64,
                    mana INTEGER DEFAULT 24,
                    max_mana INTEGER DEFAULT 24,
                    gold INTEGER DEFAULT 50,
                    stat_points INTEGER DEFAULT 2,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    battle_wins INTEGER DEFAULT 0,
                    battle_losses INTEGER DEFAULT 0,
                    boss_kills INTEGER DEFAULT 0,
                    mini_boss_kills INTEGER DEFAULT 0,
                    physical_resistance DECIMAL DEFAULT 0.0,
                    magic_resistance DECIMAL DEFAULT 0.0
                )
            """)
            
            # Таблица инвентаря
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_inventory (
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
            
            # Таблица логов
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
            
            # Индексы (для скорости)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_inventory_user_item ON player_inventory (user_id, item_key)")
            
            conn.commit()
            print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка init_db: {e}")
    finally:
        conn.close()

def apply_regeneration(character):
    """
    Применение регенерации:
    Восстанавливает 5% от макс. здоровья и маны за каждую минуту простоя.
    """
    conn = None
    try:
        # Проверяем дату последней регенерации
        last_regeneration = character.get('last_regeneration')
        if not last_regeneration:
            # Если нет даты, ставим текущую и выходим
            conn = get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE player_characters SET last_regeneration = CURRENT_TIMESTAMP WHERE user_id = %s", (character['user_id'],))
                    conn.commit()
                conn.close()
            return character

        # Приводим к datetime если нужно
        if isinstance(last_regeneration, str):
            try:
                last_regeneration = datetime.fromisoformat(last_regeneration)
            except:
                pass

        current_time = datetime.now()
        # Разница во времени
        time_diff = current_time - last_regeneration
        minutes_passed = int(time_diff.total_seconds() // 60) # Считаем полные минуты

        # Если прошло меньше 1 минуты, ничего не делаем
        if minutes_passed < 1:
            return character
        
        # Если здоровье и мана полные, просто обновляем таймер, чтобы не копить минуты
        if character['health'] >= character['max_health'] and character['mana'] >= character['max_mana']:
            conn = get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE player_characters SET last_regeneration = CURRENT_TIMESTAMP WHERE user_id = %s", (character['user_id'],))
                    conn.commit()
                conn.close()
            return character

        # Расчет восстановления (5% за минуту)
        health_regen = int(character['max_health'] * 0.05 * minutes_passed)
        mana_regen = int(character['max_mana'] * 0.05 * minutes_passed)
        
        # Если прошло хотя бы 1 минута, но 5% это 0 (на низких уровнях), даем хотя бы 1 ед.
        if health_regen == 0 and minutes_passed > 0: health_regen = minutes_passed
        if mana_regen == 0 and minutes_passed > 0: mana_regen = minutes_passed

        new_health = min(character['max_health'], character['health'] + health_regen)
        new_mana = min(character['max_mana'], character['mana'] + mana_regen)

        # Обновляем БД
        conn = get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE player_characters 
                    SET health = %s, mana = %s, last_regeneration = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (new_health, new_mana, character['user_id']))
                conn.commit()
            conn.close()
            
            # Обновляем объект персонажа для возврата актуальных данных боту
            character['health'] = new_health
            character['mana'] = new_mana
            character['last_regeneration'] = current_time

        return character

    except Exception as e:
        print(f"❌ Ошибка при регенерации: {e}")
        if conn: conn.close()
        return character

def get_character(user_id):
    """Получение информации о персонаже с авто-регенерацией"""
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            character = cursor.fetchone()
            
            if character:
                # Обновляем last_active
                cursor.execute("UPDATE player_characters SET last_active = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
                
                # Если ранг не установлен
                if not character.get('rank'):
                    rank = calculate_rank(character['level'], character['experience'])
                    cursor.execute("UPDATE player_characters SET rank = %s WHERE user_id = %s", (rank, user_id))
                    character['rank'] = rank
                
                conn.commit()
                
                # ПРИМЕНЯЕМ РЕГЕНЕРАЦИЮ ПРИ ПОЛУЧЕНИИ
                character = apply_regeneration(character)
                
            return character
    finally:
        conn.close()

def create_character(user_id, username, character_name, race):
    conn = get_connection()
    if not conn: return False, "DB Error"
    
    if race not in RACES: return False, "Unknown Race"
    race_data = RACES[race]
    
    # Статы
    strength = race_data['strength']
    agility = race_data['agility']
    intelligence = race_data['intelligence']
    vitality = race_data['vitality']
    
    health = vitality * race_data['health_multiplier']
    mana = intelligence * race_data['mana_multiplier']
    
    # Резисты
    p_res = 0.08 if race == 'elf' else 0.0
    m_res = 0.15 if race == 'dwarf' else 0.0

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
            if cursor.fetchone(): return False, "Персонаж уже существует!"

            cursor.execute("""
                INSERT INTO player_characters 
                (user_id, character_name, race, level, experience, rank,
                 strength, agility, intelligence, vitality, health, max_health, 
                 mana, max_mana, gold, stat_points, physical_resistance, magic_resistance, last_regeneration)
                VALUES (%s, %s, %s, 1, 0, 'E', %s, %s, %s, %s, %s, %s, %s, %s, 50, 2, %s, %s, CURRENT_TIMESTAMP)
            """, (user_id, character_name, race, strength, agility, intelligence, vitality, 
                  health, health, mana, mana, p_res, m_res))
            conn.commit()
            return True, "Персонаж создан!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_character_stats(user_id, **kwargs):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            set_clauses = [f"{k} = %s" for k in kwargs.keys()]
            values = list(kwargs.values())
            values.append(user_id)
            query = f"UPDATE player_characters SET {', '.join(set_clauses)} WHERE user_id = %s"
            cursor.execute(query, values)
            conn.commit()
            return True
    except Exception as e:
        print(f"Update error: {e}")
        return False
    finally:
        conn.close()

def calculate_rank(level, experience):
    if level >= 50: return 'S'
    elif level >= 40: return 'A'
    elif level >= 30: return 'B'
    elif level >= 20: return 'C'
    elif level >= 10: return 'D'
    return 'E'

def add_experience(user_id, exp_amount):
    conn = get_connection()
    if not conn: return False, False, 0, 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT experience, level, stat_points, rank, vitality, intelligence, race FROM player_characters WHERE user_id = %s", (user_id,))
            res = cursor.fetchone()
            if not res: return False, False, 0, 0
            
            cur_exp, cur_lvl, cur_pts, cur_rank, vit, intel, race = res
            new_exp = cur_exp + exp_amount
            new_lvl = cur_lvl
            level_up = False
            pts_gained = 0
            
            # Логика уровня (N * 150)
            while True:
                needed = ((new_lvl) * (new_lvl + 1) * 150) // 2
                if new_exp >= needed:
                    new_lvl += 1
                    level_up = True
                    pts_gained += 2
                else:
                    break
            
            if level_up:
                new_rank = calculate_rank(new_lvl, new_exp)
                race_info = RACES.get(race, RACES['human'])
                # При уровне увеличиваем макс ХП и МП
                new_max_hp = vit * race_info['health_multiplier'] + (new_lvl * 5) 
                new_max_mp = intel * race_info['mana_multiplier'] + (new_lvl * 2)
                
                cursor.execute("""
                    UPDATE player_characters 
                    SET experience=%s, level=%s, stat_points=stat_points+%s, rank=%s,
                        max_health=%s, max_mana=%s, health=%s, mana=%s
                    WHERE user_id=%s
                """, (new_exp, new_lvl, pts_gained, new_rank, new_max_hp, new_max_mp, new_max_hp, new_max_mp, user_id))
            else:
                cursor.execute("UPDATE player_characters SET experience=%s WHERE user_id=%s", (new_exp, user_id))
                
            conn.commit()
            return True, level_up, new_lvl, pts_gained
    finally:
        conn.close()

def add_stat_point(user_id, stat_type):
    conn = get_connection()
    if not conn: return False, "DB Error"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT stat_points, vitality, race FROM player_characters WHERE user_id=%s", (user_id,))
            data = cursor.fetchone()
            if not data or data[0] < 1: return False, "Нет очков"
            
            if stat_type == 'vitality':
                race_mult = RACES[data[2]]['health_multiplier']
                cursor.execute(f"UPDATE player_characters SET vitality=vitality+1, stat_points=stat_points-1, max_health=max_health+{race_mult}, health=health+{race_mult} WHERE user_id=%s", (user_id,))
            elif stat_type in ['strength', 'agility', 'intelligence']:
                # Интеллект тоже должен давать ману
                extra_sql = ""
                if stat_type == 'intelligence':
                    race_mult = RACES[data[2]]['mana_multiplier']
                    extra_sql = f", max_mana=max_mana+{race_mult}, mana=mana+{race_mult}"
                
                cursor.execute(f"UPDATE player_characters SET {stat_type}={stat_type}+1, stat_points=stat_points-1 {extra_sql} WHERE user_id=%s", (user_id,))
            else:
                return False, "Неверный стат"
            conn.commit()
            return True, "Успех"
    finally:
        conn.close()

def add_gold(user_id, amount):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET gold=gold+%s WHERE user_id=%s", (amount, user_id))
            conn.commit()
            return True
    finally:
        conn.close()

def increment_boss_kills(user_id, is_mini_boss=False):
    conn = get_connection()
    if not conn: return False
    col = "mini_boss_kills" if is_mini_boss else "boss_kills"
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"UPDATE player_characters SET {col}={col}+1 WHERE user_id=%s", (user_id,))
            conn.commit()
            return True
    finally:
        conn.close()

def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=None):
    conn = get_connection()
    if not conn: return False, "DB Error"
    if effect_amount is None: effect_amount = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT gold FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if not res or res[0] < price: return False, f"Нужно {price} золота"
            
            cursor.execute("UPDATE player_characters SET gold=gold-%s WHERE user_id=%s", (price, user_id))
            
            cursor.execute("SELECT id FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            exist = cursor.fetchone()
            if exist:
                cursor.execute("UPDATE player_inventory SET quantity=quantity+1 WHERE id=%s", (exist[0],))
            else:
                cursor.execute("""
                    INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount)
                    VALUES (%s, %s, %s, %s, 1, %s)
                """, (user_id, item_key, item_type, item_name, effect_amount))
            conn.commit()
            return True, f"Куплено: {item_name}"
    finally:
        conn.close()

def get_inventory(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT item_key, item_type, item_name, SUM(quantity) as quantity, MAX(effect_amount) as effect_amount
                FROM player_inventory WHERE user_id=%s AND quantity > 0
                GROUP BY item_key, item_type, item_name
                ORDER BY item_type
            """, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def use_item(user_id, item_key, item_type, item_name, effect_amount):
    conn = get_connection()
    if not conn: return False, "DB Error"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s AND quantity > 0 LIMIT 1", (user_id, item_key))
            item = cursor.fetchone()
            if not item: return False, "Предмет не найден"
            
            item_id, qty = item
            
            if 'health' in item_key:
                cursor.execute("UPDATE player_characters SET health = LEAST(max_health, health + %s) WHERE user_id=%s", (effect_amount, user_id))
            elif 'mana' in item_key:
                cursor.execute("UPDATE player_characters SET mana = LEAST(max_mana, mana + %s) WHERE user_id=%s", (effect_amount, user_id))
            
            if qty > 1:
                cursor.execute("UPDATE player_inventory SET quantity = quantity - 1 WHERE id=%s", (item_id,))
            else:
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
            conn.commit()
            return True, f"Использовано: {item_name}"
    finally:
        conn.close()

def log_battle(user_id, enemy_type, enemy_name, result, damage_dealt=0, damage_taken=0, gold_earned=0, experience_earned=0, is_boss=False, is_mini_boss=False):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO battle_logs (user_id, enemy_type, enemy_name, result, damage_dealt, damage_taken, gold_earned, experience_earned, is_boss, is_mini_boss)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, enemy_type, enemy_name, result, damage_dealt, damage_taken, gold_earned, experience_earned, is_boss, is_mini_boss))
            conn.commit()
    finally:
        conn.close()

def get_top_players(limit=10):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT character_name, race, level, rank, experience, battle_wins, boss_kills, gold
                FROM player_characters ORDER BY level DESC, experience DESC, battle_wins DESC LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_all_races():
    return RACES
