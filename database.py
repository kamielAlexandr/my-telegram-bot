import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- КОНСТАНТЫ ИГРЫ ---
RACES = {
    "human": {
        "name": "Человек",
        "strength": 10, "agility": 10, "intelligence": 10, "vitality": 10,
        "health_multiplier": 10, "mana_multiplier": 5,
        "racial_ability": "Сбалансированность"
    },
    "elf": {
        "name": "Эльф",
        "strength": 6, "agility": 15, "intelligence": 12, "vitality": 7,
        "health_multiplier": 8, "mana_multiplier": 8,
        "racial_ability": "Высокая точность и уклонение"
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 14, "agility": 5, "intelligence": 6, "vitality": 15,
        "health_multiplier": 12, "mana_multiplier": 3,
        "racial_ability": "Высокое здоровье"
    },
    "orc": {
        "name": "Орк",
        "strength": 16, "agility": 8, "intelligence": 4, "vitality": 12,
        "health_multiplier": 11, "mana_multiplier": 2,
        "racial_ability": "Огромная физическая сила"
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
            print(f"❌ DB Error: {e}")
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
                    strength INTEGER DEFAULT 10,
                    agility INTEGER DEFAULT 10,
                    intelligence INTEGER DEFAULT 10,
                    vitality INTEGER DEFAULT 10,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    mana INTEGER DEFAULT 50,
                    max_mana INTEGER DEFAULT 50,
                    gold INTEGER DEFAULT 50,
                    stat_points INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    battle_wins INTEGER DEFAULT 0,
                    battle_losses INTEGER DEFAULT 0,
                    boss_kills INTEGER DEFAULT 0
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
                    effect_amount INTEGER DEFAULT 0
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
    """Регенерация: 5% HP/MP в минуту"""
    if not character: return None
    last_regen = character.get('last_regeneration')
    if not last_regen: 
        update_regeneration_timestamp(character['user_id'])
        return character

    now = datetime.now()
    minutes_passed = int((now - last_regen).total_seconds() // 60)

    if minutes_passed < 1: return character

    max_hp = character['max_health']
    max_mana = character['max_mana']
    
    # Если полные, просто обновляем время
    if character['health'] >= max_hp and character['mana'] >= max_mana:
        update_regeneration_timestamp(character['user_id'])
        return character

    hp_regen = int((max_hp * 0.05) * minutes_passed)
    mana_regen = int((max_mana * 0.05) * minutes_passed)

    new_hp = min(max_hp, character['health'] + hp_regen)
    new_mana = min(max_mana, character['mana'] + mana_regen)

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
                character['health'] = new_hp
                character['mana'] = new_mana
                character['last_regeneration'] = now
        finally:
            conn.close()
    return character

def update_regeneration_timestamp(user_id):
    conn = get_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET last_regeneration = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
            conn.commit()
        conn.close()

def get_character(user_id):
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            character = cursor.fetchone()
            if character: character = apply_regeneration(character)
            return character
    finally:
        conn.close()

def create_character(user_id, username, character_name, race):
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    race_data = RACES.get(race)
    
    # Стартовые статы
    hp = race_data['vitality'] * race_data['health_multiplier']
    mana = race_data['intelligence'] * race_data['mana_multiplier']

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
            if cursor.fetchone(): return False, "Персонаж уже существует"

            cursor.execute("""
                INSERT INTO player_characters 
                (user_id, character_name, race, strength, agility, intelligence, vitality, 
                 health, max_health, mana, max_mana, last_regeneration, gold, stat_points, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 100, 5, 'E')
            """, (user_id, character_name, race, 
                  race_data['strength'], race_data['agility'], race_data['intelligence'], race_data['vitality'],
                  hp, hp, mana, mana))
            conn.commit()
            return True, "Успех"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_stats(user_id, **kwargs):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            set_clauses = [f"{k} = %s" for k in kwargs.keys()]
            values = list(kwargs.values())
            values.append(user_id)
            cursor.execute(f"UPDATE player_characters SET {', '.join(set_clauses)} WHERE user_id = %s", values)
            conn.commit()
    finally:
        conn.close()

def add_experience(user_id, amount):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT experience, level, stat_points FROM player_characters WHERE user_id = %s", (user_id,))
            data = cursor.fetchone()
            if not data: return
            
            cur_exp, cur_lvl, cur_pts = data
            new_exp = cur_exp + amount
            new_lvl = cur_lvl
            new_pts = cur_pts
            
            # Простой расчет уровня: Уровень * 150 опыта
            while True:
                needed = (new_lvl * (new_lvl + 1) * 150) // 2
                if new_exp >= needed:
                    new_lvl += 1
                    new_pts += 3 # 3 очка за уровень
                else:
                    break
            
            if new_lvl > cur_lvl:
                # При левелапе восстанавливаем здоровье
                cursor.execute("""
                    UPDATE player_characters SET experience=%s, level=%s, stat_points=%s, health=max_health, mana=max_mana 
                    WHERE user_id=%s
                """, (new_exp, new_lvl, new_pts, user_id))
            else:
                cursor.execute("UPDATE player_characters SET experience=%s WHERE user_id=%s", (new_exp, user_id))
            conn.commit()
    finally:
        conn.close()

def add_stat_point(user_id, stat):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT stat_points, race, vitality FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if not res or res[0] < 1: return False
            
            if stat == 'vitality':
                # Живучесть увеличивает макс ХП
                race_mult = RACES[res[1]]['health_multiplier']
                cursor.execute(f"UPDATE player_characters SET vitality=vitality+1, stat_points=stat_points-1, max_health=max_health+{race_mult}, health=health+{race_mult} WHERE user_id=%s", (user_id,))
            else:
                cursor.execute(f"UPDATE player_characters SET {stat}={stat}+1, stat_points=stat_points-1 WHERE user_id=%s", (user_id,))
            conn.commit()
            return True
    finally:
        conn.close()

# --- МАГАЗИН И ИНВЕНТАРЬ ---
def buy_item(user_id, key, name, price, effect):
    conn = get_connection()
    if not conn: return False, "Ошибка"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT gold FROM player_characters WHERE user_id=%s", (user_id,))
            gold = cursor.fetchone()[0]
            if gold < price: return False, "Недостаточно золота"
            
            cursor.execute("UPDATE player_characters SET gold=gold-%s WHERE user_id=%s", (price, user_id))
            
            cursor.execute("SELECT id FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, key))
            exist = cursor.fetchone()
            if exist:
                cursor.execute("UPDATE player_inventory SET quantity=quantity+1 WHERE id=%s", (exist[0],))
            else:
                cursor.execute("INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount) VALUES (%s, %s, 'potion', %s, 1, %s)", (user_id, key, name, effect))
            conn.commit()
            return True, "Куплено!"
    finally:
        conn.close()

def get_inventory(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_inventory WHERE user_id=%s AND quantity > 0", (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def use_item(user_id, key):
    conn = get_connection()
    if not conn: return False, "Ошибка"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity, effect_amount, item_name FROM player_inventory WHERE user_id=%s AND item_key=%s AND quantity > 0 LIMIT 1", (user_id, key))
            item = cursor.fetchone()
            if not item: return False, "Предмет не найден"
            
            val = item[2]
            if 'health' in key:
                cursor.execute("UPDATE player_characters SET health = LEAST(max_health, health + %s) WHERE user_id=%s", (val, user_id))
            elif 'mana' in key:
                cursor.execute("UPDATE player_characters SET mana = LEAST(max_mana, mana + %s) WHERE user_id=%s", (val, user_id))
            
            if item[1] > 1:
                cursor.execute("UPDATE player_inventory SET quantity=quantity-1 WHERE id=%s", (item[0],))
            else:
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item[0],))
            conn.commit()
            return True, f"Использован {item[3]}"
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
