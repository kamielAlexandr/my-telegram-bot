import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- КОНСТАНТЫ РАС ---
RACES = {
    "human": {
        "name": "Человек",
        "strength": 8, "agility": 8, "intelligence": 8, "vitality": 8,
        "health_multiplier": 8, "mana_multiplier": 3,
    },
    "elf": {
        "name": "Эльф",
        "strength": 6, "agility": 12, "intelligence": 10, "vitality": 6,
        "health_multiplier": 6, "mana_multiplier": 6,
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 11, "agility": 5, "intelligence": 7, "vitality": 10,
        "health_multiplier": 10, "mana_multiplier": 2,
    },
    "orc": {
        "name": "Орк",
        "strength": 13, "agility": 7, "intelligence": 5, "vitality": 9,
        "health_multiplier": 9, "mana_multiplier": 1.5,
    }
}

def get_connection():
    """Создание подключения к PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Ошибка: Не задан DATABASE_URL")
        return None
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
            # 1. Таблица персонажей
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
                    physical_resistance DECIMAL DEFAULT 0.0,
                    magic_resistance DECIMAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    battle_wins INTEGER DEFAULT 0,
                    battle_losses INTEGER DEFAULT 0,
                    boss_kills INTEGER DEFAULT 0,
                    mini_boss_kills INTEGER DEFAULT 0
                )
            """)
            
            # 2. Таблица инвентаря
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
            
            # Индексы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON player_inventory (user_id, item_key)")
            
            conn.commit()
            print("✅ База данных инициализирована (Dark Fantasy RPG).")
    except Exception as e:
        print(f"❌ Ошибка init_db: {e}")
    finally:
        conn.close()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def apply_regeneration(character):
    """Регенерация HP и MP со временем (5% в минуту)"""
    try:
        last_regen = character.get('last_regeneration')
        if not last_regen: return character

        if isinstance(last_regen, str):
            last_regen = datetime.fromisoformat(last_regen)

        current_time = datetime.now()
        minutes_passed = int((current_time - last_regen).total_seconds() // 60)

        if minutes_passed < 1: return character
        
        # Если здоровье полное, просто обновляем таймер
        if character['health'] >= character['max_health'] and character['mana'] >= character['max_mana']:
            update_character_stats(character['user_id'], last_regeneration=current_time)
            return character

        hp_regen = int(character['max_health'] * 0.05 * minutes_passed)
        mp_regen = int(character['max_mana'] * 0.05 * minutes_passed)
        
        # Гарантированный минимум регена 1 ед, если прошло время
        if hp_regen == 0 and minutes_passed > 0: hp_regen = minutes_passed
        if mp_regen == 0 and minutes_passed > 0: mp_regen = minutes_passed

        new_hp = min(character['max_health'], character['health'] + hp_regen)
        new_mp = min(character['max_mana'], character['mana'] + mp_regen)

        update_character_stats(character['user_id'], health=new_hp, mana=new_mp, last_regeneration=current_time)
        
        character['health'] = new_hp
        character['mana'] = new_mp
        return character
    except Exception as e:
        print(f"Regen error: {e}")
        return character

def calculate_rank(level):
    if level >= 55: return 'S'
    elif level >= 45: return 'A'
    elif level >= 35: return 'B'
    elif level >= 25: return 'C'
    elif level >= 15: return 'D'
    return 'E'

# --- ОСНОВНЫЕ ФУНКЦИИ ---

def get_character(user_id):
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            char = cursor.fetchone()
            if char:
                # Обновляем активность
                cursor.execute("UPDATE player_characters SET last_active = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
                conn.commit()
                
                # Применяем реген
                char = apply_regeneration(char)
                
                # Проверяем ранг
                actual_rank = calculate_rank(char['level'])
                if char['rank'] != actual_rank:
                    update_character_stats(user_id, rank=actual_rank)
                    char['rank'] = actual_rank
            return char
    finally:
        conn.close()

def create_character(user_id, username, char_name, race):
    conn = get_connection()
    if not conn: return False
    
    race_data = RACES.get(race, RACES['human'])
    hp = race_data['vitality'] * race_data['health_multiplier']
    mp = race_data['intelligence'] * race_data['mana_multiplier']
    
    p_res = 0.05 if race == 'orc' else 0.0
    m_res = 0.10 if race == 'dwarf' else 0.0
    if race == 'elf': m_res = 0.05

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
            if cursor.fetchone(): return False 

            cursor.execute("""
                INSERT INTO player_characters 
                (user_id, character_name, race, strength, agility, intelligence, vitality, 
                 health, max_health, mana, max_mana, physical_resistance, magic_resistance, gold)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 50)
            """, (user_id, char_name, race, 
                  race_data['strength'], race_data['agility'], race_data['intelligence'], race_data['vitality'],
                  hp, hp, mp, mp, p_res, m_res))
            conn.commit()
            return True
    except Exception as e:
        print(f"Create error: {e}")
        return False
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

# --- ИНВЕНТАРЬ И МАГАЗИН ---

def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=0):
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    
    try:
        with conn.cursor() as cursor:
            # 1. Проверяем деньги
            if price > 0:
                cursor.execute("SELECT gold FROM player_characters WHERE user_id=%s", (user_id,))
                res = cursor.fetchone()
                if not res or res[0] < price:
                    return False, f"Не хватает золота! Нужно {price}g"
                
                cursor.execute("UPDATE player_characters SET gold = gold - %s WHERE user_id=%s", (price, user_id))

            # 2. Добавляем в инвентарь (или увеличиваем кол-во)
            cursor.execute("SELECT id FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            exist = cursor.fetchone()
            if exist:
                cursor.execute("UPDATE player_inventory SET quantity = quantity + 1 WHERE id=%s", (exist[0],))
            else:
                cursor.execute("""
                    INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount)
                    VALUES (%s, %s, %s, %s, 1, %s)
                """, (user_id, item_key, item_type, item_name, effect_amount))

            # 3. Применяем бонусы экипировки (навсегда)
            msg_extra = ""
            if item_type == 'weapon':
                cursor.execute("UPDATE player_characters SET strength = strength + %s WHERE user_id=%s", (effect_amount, user_id))
                msg_extra = f"\n💪 Сила увеличилась на +{effect_amount}!"
            elif item_type == 'armor':
                hp_bonus = effect_amount
                vit_bonus = max(1, int(effect_amount / 10))
                # ВАЖНО: Увеличиваем И max_health, И текущее health
                cursor.execute("UPDATE player_characters SET max_health = max_health + %s, health = health + %s, vitality = vitality + %s WHERE user_id=%s", (hp_bonus, hp_bonus, vit_bonus, user_id))
                msg_extra = f"\n🛡️ HP увеличено на +{hp_bonus}!"
            elif item_type in ['artifact', 'acc']:
                int_bonus = effect_amount
                mp_bonus = int_bonus * 5
                cursor.execute("UPDATE player_characters SET intelligence = intelligence + %s, max_mana = max_mana + %s, mana = mana + %s WHERE user_id=%s", (int_bonus, mp_bonus, mp_bonus, user_id))
                msg_extra = f"\n🧠 Интеллект +{int_bonus}"

            conn.commit()
            action = "Куплено" if price > 0 else "Получено"
            return True, f"{action}: {item_name}{msg_extra}"

    except Exception as e:
        print(f"Buy error: {e}")
        return False, "Ошибка при покупке"
    finally:
        conn.close()


def use_item(user_id, item_key, item_type, item_name, effect_amount):
    """Использование расходников (еда, зелья, материалы)"""
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s AND quantity > 0", (user_id, item_key))
            item = cursor.fetchone()
            if not item: return False, "Предмета нет в наличии"
            
            item_id, qty = item
            msg_effect = ""

            # Эффекты только для еды и зелий
            if item_type in ['food', 'potion']:
                if 'mana' in item_key or 'mp' in item_key:
                    cursor.execute("UPDATE player_characters SET mana = LEAST(max_mana, mana + %s) WHERE user_id=%s", (effect_amount, user_id))
                    msg_effect = f"\n🌀 Мана +{effect_amount}"
                else:
                    cursor.execute("UPDATE player_characters SET health = LEAST(max_health, health + %s) WHERE user_id=%s", (effect_amount, user_id))
                    msg_effect = f"\n❤️ Здоровье +{effect_amount}"
            
            # Списываем предмет
            if qty > 1:
                cursor.execute("UPDATE player_inventory SET quantity = quantity - 1 WHERE id=%s", (item_id,))
            else:
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
            
            conn.commit()
            return True, f"Использовано: {item_name}{msg_effect}"

    except Exception as e:
        print(f"Use item error: {e}")
        return False, "Ошибка использования"
    finally:
        conn.close()

def get_inventory(user_id):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT item_key, item_type, item_name, quantity, effect_amount FROM player_inventory WHERE user_id=%s ORDER BY item_type", (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

# --- ПРОКАЧКА ---

def add_experience(user_id, exp_amount):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT experience, level, stat_points FROM player_characters WHERE user_id=%s", (user_id,))
            data = cursor.fetchone()
            if not data: return

            cur_exp, cur_lvl, pts = data
            new_exp = cur_exp + exp_amount
            
            # Цикл для повышения нескольких уровней сразу
            leveled_up = False
            while True:
                needed = (cur_lvl * (cur_lvl + 1) * 150) // 2
                if new_exp >= needed:
                    cur_lvl += 1
                    pts += 2
                    leveled_up = True
                else:
                    break
            
            if leveled_up:
                cursor.execute("""
                    UPDATE player_characters 
                    SET experience=%s, level=%s, stat_points=%s, health=max_health, mana=max_mana 
                    WHERE user_id=%s
                """, (new_exp, cur_lvl, pts, user_id))
            else:
                cursor.execute("UPDATE player_characters SET experience=%s WHERE user_id=%s", (new_exp, user_id))
            
            conn.commit()
    finally:
        conn.close()

def add_stat_point(user_id, stat_type):
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT stat_points, race FROM player_characters WHERE user_id=%s", (user_id,))
            data = cursor.fetchone()
            if not data or data[0] < 1: return False, "Нет очков навыков!"

            race = data[1]
            race_info = RACES.get(race, RACES['human'])
            
            extra_sql = ""
            if stat_type == 'vitality':
                bonus_hp = race_info['health_multiplier']
                extra_sql = f", max_health = max_health + {bonus_hp}, health = health + {bonus_hp}"
            elif stat_type == 'intelligence':
                bonus_mp = race_info['mana_multiplier']
                extra_sql = f", max_mana = max_mana + {bonus_mp}, mana = mana + {bonus_mp}"
            
            valid_stats = ['strength', 'agility', 'intelligence', 'vitality']
            if stat_type not in valid_stats: return False, "Неверный стат"

            sql = f"UPDATE player_characters SET {stat_type} = {stat_type} + 1, stat_points = stat_points - 1 {extra_sql} WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            conn.commit()
            return True, "Успешно!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def add_gold(user_id, amount):
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET gold = gold + %s WHERE user_id=%s", (amount, user_id))
            conn.commit()
    finally:
        conn.close()

def increment_boss_kills(user_id, is_mini_boss=False):
    conn = get_connection()
    if not conn: return
    col = "mini_boss_kills" if is_mini_boss else "boss_kills"
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"UPDATE player_characters SET {col} = {col} + 1 WHERE user_id=%s", (user_id,))
            conn.commit()
    finally:
        conn.close()

def get_top_players(limit=10):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT character_name, race, level, battle_wins, boss_kills, gold 
                FROM player_characters 
                ORDER BY level DESC, battle_wins DESC 
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_all_users():
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM player_characters")
            return [r[0] for r in cursor.fetchall()]
    finally:
        conn.close()
        
def remove_item(user_id, item_key, quantity):
    """Списывает указанное количество предметов (для крафта)"""
    conn = get_connection()
    if not conn: return False
    
    try:
        with conn.cursor() as cursor:
            # Проверяем, есть ли предмет и хватает ли его
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            res = cursor.fetchone()
            
            if not res: return False # Предмета нет
            
            item_id, current_qty = res
            
            if current_qty < quantity:
                return False # Не хватает количества
            
            # Списываем
            if current_qty == quantity:
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
            else:
                cursor.execute("UPDATE player_inventory SET quantity = quantity - %s WHERE id=%s", (quantity, item_id))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Remove item error: {e}")
        return False
    finally:
        conn.close()
