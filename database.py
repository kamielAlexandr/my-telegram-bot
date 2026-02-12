import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- КОНСТАНТЫ ИГРЫ ---
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
    if not database_url:
        return None
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except:
        try:
            conn = psycopg2.connect(database_url)
            return conn
        except Exception as e:
            print(f"❌ Ошибка подключения БД: {e}")
            return None

def init_db():
    """Инициализация таблиц"""
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
            
            # Индексы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON player_inventory (user_id)")
            
            conn.commit()
            print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка init_db: {e}")
    finally:
        conn.close()

def apply_regeneration(character):
    """
    Рассчитывает и применяет регенерацию:
    +5% HP и +5% Mana за каждую минуту простоя.
    """
    if not character: return None

    last_regen = character.get('last_regeneration')
    if not last_regen: 
        # Если времени нет, ставим текущее
        update_regeneration_timestamp(character['user_id'])
        return character

    now = datetime.now()
    # Разница во времени
    time_diff = now - last_regen
    minutes_passed = int(time_diff.total_seconds() // 60) # Сколько минут прошло

    # Если прошло меньше минуты, регенерации нет
    if minutes_passed < 1:
        return character

    max_hp = character['max_health']
    max_mana = character['max_mana']
    current_hp = character['health']
    current_mana = character['mana']

    # Если уже фулл, просто обновляем таймер, чтобы не копить минуты зря
    if current_hp >= max_hp and current_mana >= max_mana:
        update_regeneration_timestamp(character['user_id'])
        return character

    # Формула: 5% от максимума * количество минут
    hp_regen = int((max_hp * 0.05) * minutes_passed)
    mana_regen = int((max_mana * 0.05) * minutes_passed)

    new_hp = min(max_hp, current_hp + hp_regen)
    new_mana = min(max_mana, current_mana + mana_regen)

    # Сохраняем в БД
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE player_characters 
                    SET health = %s, mana = %s, last_regeneration = %s
                    WHERE user_id = %s
                """, (new_hp, new_mana, now, character['user_id']))
                conn.commit()
                
                # Обновляем объект персонажа для возврата
                character['health'] = new_hp
                character['mana'] = new_mana
                character['last_regeneration'] = now
        finally:
            conn.close()

    return character

def update_regeneration_timestamp(user_id):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE player_characters SET last_regeneration = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
                conn.commit()
        finally:
            conn.close()

def get_character(user_id):
    """Получает персонажа и СРАЗУ применяет регенерацию"""
    conn = get_connection()
    if not conn: return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            character = cursor.fetchone()
            
            if character:
                # Применяем регенерацию перед тем как отдать данные боту
                character = apply_regeneration(character)
            
            return character
    finally:
        conn.close()

def create_character(user_id, username, character_name, race):
    conn = get_connection()
    if not conn: return False, "DB Error"
    
    race_data = RACES.get(race)
    if not race_data: return False, "Invalid Race"

    # Расчет начальных статов
    hp = race_data['vitality'] * race_data['health_multiplier']
    mana = race_data['intelligence'] * race_data['mana_multiplier']
    
    # Бонусы сопротивления
    phys_res = 0.08 if race == 'elf' else 0.0
    magic_res = 0.15 if race == 'dwarf' else 0.0

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
            if cursor.fetchone(): return False, "Персонаж уже существует"

            cursor.execute("""
                INSERT INTO player_characters 
                (user_id, character_name, race, strength, agility, intelligence, vitality, 
                 health, max_health, mana, max_mana, physical_resistance, magic_resistance, 
                 last_regeneration, gold, stat_points, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 50, 2, 'E')
            """, (user_id, character_name, race, 
                  race_data['strength'], race_data['agility'], race_data['intelligence'], race_data['vitality'],
                  hp, hp, mana, mana, phys_res, magic_res))
            conn.commit()
            return True, "Success"
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
        print(f"Error update: {e}")
        return False
    finally:
        conn.close()

def add_stat_point(user_id, stat_type):
    conn = get_connection()
    if not conn: return False, "DB Error"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT stat_points, vitality, race, health, max_health FROM player_characters WHERE user_id = %s", (user_id,))
            data = cursor.fetchone()
            if not data or data[0] < 1: return False, "Нет очков"
            
            # Логика для живучести (увеличивает HP)
            if stat_type == 'vitality':
                race_mult = RACES[data[2]]['health_multiplier']
                cursor.execute(f"""
                    UPDATE player_characters 
                    SET vitality = vitality + 1, stat_points = stat_points - 1,
                        max_health = max_health + %s, health = health + %s
                    WHERE user_id = %s
                """, (race_mult, race_mult, user_id))
            elif stat_type in ['strength', 'agility', 'intelligence']:
                cursor.execute(f"UPDATE player_characters SET {stat_type} = {stat_type} + 1, stat_points = stat_points - 1 WHERE user_id = %s", (user_id,))
            else:
                return False, "Неверный стат"
                
            conn.commit()
            return True, "Успех"
    finally:
        conn.close()

def add_experience(user_id, amount):
    conn = get_connection()
    if not conn: return False, False, 0, 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT experience, level, stat_points FROM player_characters WHERE user_id = %s", (user_id,))
            data = cursor.fetchone()
            if not data: return False, False, 0, 0
            
            cur_exp, cur_lvl, _ = data
            new_exp = cur_exp + amount
            
            # Формула уровня: N * 150
            needed = cur_lvl * 150
            level_up = False
            points = 0
            
            new_lvl = cur_lvl
            while new_exp >= needed:
                new_exp -= 0 # В вашей логике опыт накопительный, формула сложнее.
                # Упростим: если накопленный опыт > (N*(N+1)*150)/2
                total_needed = (new_lvl * (new_lvl + 1) * 150) // 2
                if new_exp >= total_needed:
                    new_lvl += 1
                    points += 2
                    level_up = True
                else:
                    break
            
            if level_up:
                cursor.execute("""
                    UPDATE player_characters 
                    SET experience = %s, level = %s, stat_points = stat_points + %s,
                        health = max_health, mana = max_mana 
                    WHERE user_id = %s
                """, (new_exp, new_lvl, points, user_id))
            else:
                cursor.execute("UPDATE player_characters SET experience = %s WHERE user_id = %s", (new_exp, user_id))
                
            conn.commit()
            return True, level_up, new_lvl, points
    finally:
        conn.close()

# Функции инвентаря и магазина
def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=0):
    conn = get_connection()
    if not conn: return False, "DB Error"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT gold FROM player_characters WHERE user_id = %s", (user_id,))
            res = cursor.fetchone()
            if not res or res[0] < price: return False, "Нет золота"
            
            cursor.execute("UPDATE player_characters SET gold = gold - %s WHERE user_id = %s", (price, user_id))
            
            # Проверяем наличие
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            exist = cursor.fetchone()
            
            if exist:
                cursor.execute("UPDATE player_inventory SET quantity = quantity + 1 WHERE id=%s", (exist[0],))
            else:
                cursor.execute("""
                    INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount)
                    VALUES (%s, %s, %s, %s, 1, %s)
                """, (user_id, item_key, item_type, item_name, effect_amount))
            conn.commit()
            return True, "Куплено"
    finally:
        conn.close()

def get_inventory(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_inventory WHERE user_id = %s AND quantity > 0", (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def use_item(user_id, item_key):
    conn = get_connection()
    if not conn: return False, "DB Error"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity, effect_amount, item_type, item_name FROM player_inventory WHERE user_id=%s AND item_key=%s AND quantity > 0 LIMIT 1", (user_id, item_key))
            item = cursor.fetchone()
            if not item: return False, "Нет предмета"
            
            item_id, qty, effect, itype, name = item
            
            # Эффекты
            msg = f"Использован {name}"
            if 'health_potion' in item_key:
                cursor.execute("UPDATE player_characters SET health = LEAST(max_health, health + %s) WHERE user_id=%s", (effect, user_id))
                msg += f" (+{effect} HP)"
            elif 'mana_potion' in item_key:
                cursor.execute("UPDATE player_characters SET mana = LEAST(max_mana, mana + %s) WHERE user_id=%s", (effect, user_id))
                msg += f" (+{effect} MP)"
            
            # Списание
            if qty > 1:
                cursor.execute("UPDATE player_inventory SET quantity = quantity - 1 WHERE id=%s", (item_id,))
            else:
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
                
            conn.commit()
            return True, msg
    finally:
        conn.close()

def get_top_players(limit=10):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT character_name, level, rank, battle_wins, boss_kills, gold 
                FROM player_characters ORDER BY level DESC, experience DESC LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    finally:
        conn.close()
