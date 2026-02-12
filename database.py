import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- КОНСТАНТЫ ИГРЫ ---
RACES = {
    "human": {
        "name": "👨 Человек",
        "strength": 8, "agility": 8, "intelligence": 8, "vitality": 8,
        "health_mult": 10, "mana_mult": 5,
        "ability": "Адаптивность (Щит +50% защиты)"
    },
    "elf": {
        "name": "🧝 Эльф",
        "strength": 5, "agility": 12, "intelligence": 10, "vitality": 5,
        "health_mult": 8, "mana_mult": 8,
        "ability": "Меткий глаз (Крит + Шанс попадания)"
    },
    "dwarf": {
        "name": "⚒️ Дварф",
        "strength": 10, "agility": 4, "intelligence": 6, "vitality": 12,
        "health_mult": 12, "mana_mult": 3,
        "ability": "Каменная кожа (Лечение + Защита)"
    },
    "orc": {
        "name": "👺 Орк",
        "strength": 13, "agility": 6, "intelligence": 3, "vitality": 10,
        "health_mult": 11, "mana_mult": 2,
        "ability": "Берсерк (Двойной урон ценой здоровья)"
    }
}

# Требования к рангам
RANKS = {
    'E': 1,
    'D': 10,
    'C': 20,
    'B': 35,
    'A': 50,
    'S': 70
}

def get_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url: return None
    try:
        return psycopg2.connect(database_url, sslmode='require')
    except:
        try:
            return psycopg2.connect(database_url)
        except Exception as e:
            print(f"❌ DB Error: {e}")
            return None

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_characters (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    character_name VARCHAR(100) NOT NULL,
                    race VARCHAR(50) NOT NULL,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    rank VARCHAR(10) DEFAULT 'E',
                    strength INTEGER, agility INTEGER, intelligence INTEGER, vitality INTEGER,
                    health INTEGER, max_health INTEGER,
                    mana INTEGER, max_mana INTEGER,
                    gold INTEGER DEFAULT 50,
                    stat_points INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    battle_wins INTEGER DEFAULT 0,
                    battle_losses INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_inventory (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    item_key VARCHAR(100) NOT NULL,
                    item_name VARCHAR(100) NOT NULL,
                    item_type VARCHAR(50),
                    quantity INTEGER DEFAULT 1,
                    effect_amount INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            print("✅ База данных готова.")
    finally:
        conn.close()

def apply_regeneration(character):
    """Регенерация: 5% в минуту"""
    if not character: return None
    last_regen = character.get('last_regeneration')
    if not last_regen:
        update_regen_time(character['user_id'])
        return character

    now = datetime.now()
    minutes = int((now - last_regen).total_seconds() // 60)
    if minutes < 1: return character

    max_hp = character['max_health']
    max_mp = character['max_mana']
    
    if character['health'] >= max_hp and character['mana'] >= max_mp:
        update_regen_time(character['user_id'])
        return character

    hp_gain = int(max_hp * 0.05 * minutes)
    mp_gain = int(max_mp * 0.05 * minutes)

    new_hp = min(max_hp, character['health'] + hp_gain)
    new_mp = min(max_mp, character['mana'] + mp_gain)

    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET health=%s, mana=%s, last_regeneration=%s WHERE user_id=%s", 
                           (new_hp, new_mp, now, character['user_id']))
            conn.commit()
        conn.close()
        
    character['health'] = new_hp
    character['mana'] = new_mp
    return character

def update_regen_time(user_id):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET last_regeneration=CURRENT_TIMESTAMP WHERE user_id=%s", (user_id,))
            conn.commit()
        conn.close()

def get_character(user_id):
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            char = cursor.fetchone()
            if char: return apply_regeneration(char)
            return None
    finally:
        conn.close()

def create_character(user_id, name, race_key):
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    race = RACES.get(race_key)
    hp = race['vitality'] * race['health_mult']
    mp = race['intelligence'] * race['mana_mult']

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM player_characters WHERE user_id=%s", (user_id,))
            if cursor.fetchone(): return False, "Герой уже существует"
            cursor.execute("""
                INSERT INTO player_characters 
                (user_id, character_name, race, strength, agility, intelligence, vitality, 
                 health, max_health, mana, max_mana, last_regeneration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (user_id, name, race_key, race['strength'], race['agility'], race['intelligence'], race['vitality'], hp, hp, mp, mp))
            conn.commit()
            return True, "Успех"
    finally:
        conn.close()

def add_stat_point(user_id, stat):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT stat_points, race FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if not res or res[0] < 1: return
            
            pts, race_key = res
            if stat == 'vitality':
                mult = RACES[race_key]['health_mult']
                cursor.execute(f"UPDATE player_characters SET vitality=vitality+1, max_health=max_health+{mult}, health=health+{mult}, stat_points=stat_points-1 WHERE user_id=%s", (user_id,))
            elif stat == 'intelligence':
                mult = RACES[race_key]['mana_mult']
                cursor.execute(f"UPDATE player_characters SET intelligence=intelligence+1, max_mana=max_mana+{mult}, mana=mana+{mult}, stat_points=stat_points-1 WHERE user_id=%s", (user_id,))
            else:
                cursor.execute(f"UPDATE player_characters SET {stat}={stat}+1, stat_points=stat_points-1 WHERE user_id=%s", (user_id,))
            conn.commit()
    finally:
        conn.close()

def calculate_new_rank(level):
    """Возвращает ранг на основе уровня"""
    for rank, req_lvl in sorted(RANKS.items(), key=lambda x: x[1], reverse=True):
        if level >= req_lvl:
            return rank
    return 'E'

def add_rewards(user_id, exp, gold):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT level, experience, stat_points, rank FROM player_characters WHERE user_id=%s", (user_id,))
            data = cursor.fetchone()
            if not data: return
            
            cur_lvl, cur_exp, cur_pts, cur_rank = data
            new_exp = cur_exp + exp
            new_lvl = cur_lvl
            
            # Накопительная система опыта
            while True:
                needed = (new_lvl * (new_lvl + 1) * 150) // 2
                if new_exp >= needed:
                    new_lvl += 1
                    cur_pts += 3
                else:
                    break
            
            new_rank = calculate_new_rank(new_lvl)
            
            update_sql = "UPDATE player_characters SET experience=%s, gold=gold+%s, battle_wins=battle_wins+1"
            params = [new_exp, gold]
            
            if new_lvl > cur_lvl:
                update_sql += ", level=%s, stat_points=%s, health=max_health, mana=max_mana, rank=%s"
                params.extend([new_lvl, cur_pts, new_rank])
                
            update_sql += " WHERE user_id=%s"
            params.append(user_id)
            
            cursor.execute(update_sql, params)
            conn.commit()
            return new_lvl > cur_lvl, new_rank
    finally:
        conn.close()

def update_hp_mp(user_id, hp, mp):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET health=%s, mana=%s WHERE user_id=%s", (hp, mp, user_id))
            conn.commit()
    finally:
        conn.close()

def get_top_players(limit=10):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT character_name, level, rank, battle_wins, gold FROM player_characters ORDER BY level DESC, experience DESC LIMIT %s", (limit,))
            return cursor.fetchall()
    finally:
        conn.close()

def buy_item(user_id, key, name, price, effect):
    conn = get_connection()
    if not conn: return False, "Ошибка"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT gold FROM player_characters WHERE user_id=%s", (user_id,))
            if cursor.fetchone()[0] < price: return False, "Не хватает золота"
            cursor.execute("UPDATE player_characters SET gold=gold-%s WHERE user_id=%s", (price, user_id))
            cursor.execute("INSERT INTO player_inventory (user_id, item_key, item_name, quantity, effect_amount) VALUES (%s, %s, %s, 1, %s)", (user_id, key, name, effect))
            conn.commit()
            return True, "Куплено"
    finally:
        conn.close()

def get_inventory(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_inventory WHERE user_id=%s", (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def use_inventory_item(user_id, item_id):
    conn = get_connection()
    if not conn: return False, "Ошибка"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT item_key, effect_amount FROM player_inventory WHERE id=%s", (item_id,))
            item = cursor.fetchone()
            if not item: return False, "Нет предмета"
            
            key, effect = item
            if 'hp' in key: cursor.execute("UPDATE player_characters SET health=LEAST(max_health, health+%s) WHERE user_id=%s", (effect, user_id))
            if 'mp' in key: cursor.execute("UPDATE player_characters SET mana=LEAST(max_mana, mana+%s) WHERE user_id=%s", (effect, user_id))
            
            cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
            conn.commit()
            return True, "Использовано"
    finally:
        conn.close()
