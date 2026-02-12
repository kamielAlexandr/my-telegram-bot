import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Константы (Остались как в твоем коде)
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
            print(f"❌ Ошибка БД: {e}")
            return None

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            # Создаем таблицу, добавив last_regeneration, если её нет
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
            
            # Инвентарь
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
            
            # Логи боев
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
            conn.commit()
            print("✅ База данных инициализирована")
    finally:
        conn.close()

# --- ЛОГИКА РЕГЕНЕРАЦИИ (НОВАЯ) ---
def apply_regeneration(character):
    """Восстанавливает 5% ХП и Маны в минуту"""
    if not character: return None
    
    last_regen = character.get('last_regeneration')
    if not last_regen:
        update_regen_timestamp(character['user_id'])
        return character

    now = datetime.now()
    # Разница во времени
    try:
        minutes_passed = int((now - last_regen).total_seconds() // 60)
    except:
        update_regen_timestamp(character['user_id'])
        return character

    if minutes_passed < 1: return character

    max_hp = character['max_health']
    max_mp = character['max_mana']
    
    if character['health'] >= max_hp and character['mana'] >= max_mp:
        update_regen_timestamp(character['user_id'])
        return character

    # 5% в минуту
    hp_gain = int(max_hp * 0.05 * minutes_passed)
    mp_gain = int(max_mp * 0.05 * minutes_passed)
    
    # Минимум 1 ед, если прошло время
    if hp_gain == 0 and minutes_passed > 0: hp_gain = minutes_passed
    if mp_gain == 0 and minutes_passed > 0: mp_gain = minutes_passed

    new_hp = min(max_hp, character['health'] + hp_gain)
    new_mp = min(max_mp, character['mana'] + mp_gain)

    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE player_characters 
                SET health=%s, mana=%s, last_regeneration=%s 
                WHERE user_id=%s
            """, (new_hp, new_mp, now, character['user_id']))
            conn.commit()
        conn.close()
        
    character['health'] = new_hp
    character['mana'] = new_mp
    return character

def update_regen_timestamp(user_id):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET last_regeneration=CURRENT_TIMESTAMP WHERE user_id=%s", (user_id,))
            conn.commit()
        conn.close()

def get_character(user_id):
    """Получает персонажа и применяет регенерацию"""
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            character = cursor.fetchone()
            
            if character:
                # Обновляем активность
                cursor.execute("UPDATE player_characters SET last_active = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
                
                # Если ранга нет
                if not character.get('rank'):
                    rank = calculate_rank(character['level'], character['experience'])
                    cursor.execute("UPDATE player_characters SET rank = %s WHERE user_id = %s", (rank, user_id))
                    character['rank'] = rank
                conn.commit()
                
                # РЕГЕНЕРАЦИЯ
                character = apply_regeneration(character)
                
            return character
    finally:
        conn.close()

# --- ОСТАЛЬНЫЕ ФУНКЦИИ (Твои оригинальные, адаптированные под DB) ---

def create_character(user_id, username, character_name, race):
    conn = get_connection()
    if not conn: return False, "DB Error"
    
    race_data = RACES.get(race)
    hp = race_data['vitality'] * race_data['health_multiplier']
    mana = race_data['intelligence'] * race_data['mana_multiplier']
    
    p_res = 0.08 if race == 'elf' else 0.0
    m_res = 0.15 if race == 'dwarf' else 0.0

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
            if cursor.fetchone(): return False, "Персонаж уже существует"

            cursor.execute("""
                INSERT INTO player_characters 
                (user_id, character_name, race, strength, agility, intelligence, vitality, 
                 health, max_health, mana, max_mana, gold, stat_points, rank, physical_resistance, magic_resistance, last_regeneration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 50, 2, 'E', %s, %s, CURRENT_TIMESTAMP)
            """, (user_id, character_name, race, 
                  race_data['strength'], race_data['agility'], race_data['intelligence'], race_data['vitality'],
                  hp, hp, mana, mana, p_res, m_res))
            conn.commit()
            return True, "Успех"
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
            cursor.execute(f"UPDATE player_characters SET {', '.join(set_clauses)} WHERE user_id = %s", values)
            conn.commit()
            return True
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
            data = cursor.fetchone()
            if not data: return False, False, 0, 0
            
            cur_exp, cur_lvl, cur_pts, cur_rank, vit, intel, race = data
            new_exp = cur_exp + exp_amount
            new_lvl = cur_lvl
            lvl_up = False
            pts_gained = 0
            
            # (Твоя формула опыта)
            while True:
                needed = ((new_lvl) * (new_lvl + 1) * 150) // 2
                if new_exp >= needed:
                    new_lvl += 1
                    lvl_up = True
                    pts_gained += 2
                else:
                    break
            
            if lvl_up:
                new_rank = calculate_rank(new_lvl, new_exp)
                r_info = RACES.get(race, RACES['human'])
                new_max_hp = vit * r_info['health_multiplier'] + (new_lvl * 5)
                new_max_mp = intel * r_info['mana_multiplier'] + (new_lvl * 2)
                
                cursor.execute("""
                    UPDATE player_characters 
                    SET experience=%s, level=%s, stat_points=stat_points+%s, rank=%s,
                        max_health=%s, max_mana=%s, health=%s, mana=%s
                    WHERE user_id=%s
                """, (new_exp, new_lvl, pts_gained, new_rank, new_max_hp, new_max_mp, new_max_hp, new_max_mp, user_id))
            else:
                cursor.execute("UPDATE player_characters SET experience=%s WHERE user_id=%s", (new_exp, user_id))
                
            conn.commit()
            return True, lvl_up, new_lvl, pts_gained
    finally:
        conn.close()

def add_stat_point(user_id, stat_type):
    conn = get_connection()
    if not conn: return False, "Ошибка"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT stat_points, vitality, race FROM player_characters WHERE user_id=%s", (user_id,))
            data = cursor.fetchone()
            if not data or data[0] < 1: return False, "Нет очков"
            
            if stat_type == 'vitality':
                race_mult = RACES[data[2]]['health_multiplier']
                cursor.execute(f"UPDATE player_characters SET vitality=vitality+1, stat_points=stat_points-1, max_health=max_health+{race_mult}, health=health+{race_mult} WHERE user_id=%s", (user_id,))
            else:
                extra = ""
                if stat_type == 'intelligence':
                    m_mult = RACES[data[2]]['mana_multiplier']
                    extra = f", max_mana=max_mana+{m_mult}, mana=mana+{m_mult}"
                cursor.execute(f"UPDATE player_characters SET {stat_type}={stat_type}+1, stat_points=stat_points-1 {extra} WHERE user_id=%s", (user_id,))
            conn.commit()
            return True, "Успех"
    finally:
        conn.close()

def add_gold(user_id, amount):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET gold=gold+%s WHERE user_id=%s", (amount, user_id))
            conn.commit()
    finally:
        conn.close()

def increment_boss_kills(user_id, is_mini_boss=False):
    conn = get_connection()
    if not conn: return
    col = "mini_boss_kills" if is_mini_boss else "boss_kills"
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"UPDATE player_characters SET {col}={col}+1 WHERE user_id=%s", (user_id,))
            conn.commit()
    finally:
        conn.close()

def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=0):
    conn = get_connection()
    if not conn: return False, "Ошибка"
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
                cursor.execute("INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount) VALUES (%s, %s, %s, %s, 1, %s)", (user_id, item_key, item_type, item_name, effect_amount))
            conn.commit()
            return True, f"Куплено: {item_name}"
    finally:
        conn.close()

def get_inventory(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT item_key, item_type, item_name, SUM(quantity) as quantity, MAX(effect_amount) as effect_amount FROM player_inventory WHERE user_id=%s AND quantity > 0 GROUP BY item_key, item_type, item_name ORDER BY item_type", (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def use_item(user_id, item_key, item_type, item_name, effect_amount):
    conn = get_connection()
    if not conn: return False, "Ошибка"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s AND quantity > 0 LIMIT 1", (user_id, item_key))
            item = cursor.fetchone()
            if not item: return False, "Нет предмета"
            
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
            return True, f"Использован {item_name}"
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
            cursor.execute("SELECT character_name, race, level, rank, experience, battle_wins, boss_kills, gold FROM player_characters ORDER BY level DESC, experience DESC, battle_wins DESC LIMIT %s", (limit,))
            return cursor.fetchall()
    finally:
        conn.close()
