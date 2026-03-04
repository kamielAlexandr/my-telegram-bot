import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json


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
    },
    "vampire": {
        "name": "Вампир",
        "strength": 10, "agility": 13, "intelligence": 8, "vitality": 4, # Мало здоровья, много ловкости
        "health_multiplier": 5, 
        "mana_multiplier": 4,
    },
    "lizardman": {
        "name": "Ящеролюд",
        "strength": 11, "agility": 8, "intelligence": 4, "vitality": 12, # Очень много ХП
        "health_multiplier": 9, 
        "mana_multiplier": 2,
    },
    "frogman": {
        "name": "Жаболюд",
        "strength": 6, "agility": 14, "intelligence": 9, "vitality": 6, # Экстремальная ловкость
        "health_multiplier": 6, 
        "mana_multiplier": 4,
    },
    # --- НОВЫЕ РАСЫ ---
    "leprechaun": {
        "name": "Лепрекон",
        "strength": 5, "agility": 12, "intelligence": 11, "vitality": 6, # Слаб физически, но хитер
        "health_multiplier": 6, 
        "mana_multiplier": 5,
    },
    "undead": {
        "name": "Нежить",
        "strength": 12, "agility": 4, "intelligence": 7, "vitality": 15, # Медленный, но огромный запас ХП
        "health_multiplier": 11, 
        "mana_multiplier": 2,
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
            # 1. Создание основной таблицы (если нет)
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
            
            # 2. Создание таблицы инвентаря (если нет)
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON player_inventory (user_id, item_key)")

            # --- 3. АВТОМАТИЧЕСКОЕ ДОБАВЛЕНИЕ НОВЫХ КОЛОНОК (МИГРАЦИЯ) ---
            # Мы пытаемся добавить колонки. Если они есть — команда просто игнорируется или падает (мы ловим ошибку).
            # Это "грязный", но простой способ обновить структуру без сложных миграций.
            
            columns_to_add = [
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_target VARCHAR(50)",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_type VARCHAR(20)",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_goal INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_progress INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_reward_gold INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_reward_exp INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_quest_date DATE",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS daily_quests_data TEXT",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_refresh_date DATE",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS elf_magic_type VARCHAR(20)",
                # В списке columns_to_add:
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS guild_reputation INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_honey_collection TIMESTAMP",
                # --- НОВАЯ СТРОЧКА ДЛЯ РЕЙДОВ ---
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_raid_attack TIMESTAMP",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS elf_active_spell VARCHAR(50)",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quests_completed_today INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS guild_reputation INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_honey_collection TIMESTAMP"
            ]
            
            for sql in columns_to_add:
                try:
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    # Если колонка уже есть или БД не поддерживает IF NOT EXISTS (старый postgres),
                    # просто откатываем транзакцию и идем дальше
                    conn.rollback() 

            conn.commit()
            print("✅ База данных обновлена (структура проверена).")
    except Exception as e:
        print(f"❌ Ошибка init_db: {e}")
    finally:
        conn.close()
# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def apply_regeneration(character):
    """Регенерация HP и MP со временем. Новичкам (1-10 ур) - 15% в минуту, остальным - 5%"""
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

        # === НОВАЯ ЛОГИКА РЕГЕНЕРАЦИИ ПО УРОВНЯМ ===
        lvl = character.get('level', 1)
        vit = character.get('vitality', 10)
        
        if lvl <= 10:
            base_hp_regen = 0.15  # 15% для новичков (1-10 ур)
            base_mp_regen = 0.15  # 15% маны для новичков
        else:
            base_hp_regen = 0.05  # 5% для опытных (11+ ур)
            base_mp_regen = 0.05  # 5% маны для опытных

        # К базовому % прибавляем бонус от Живучести (0.2% за каждую единицу)
        hp_regen_percent = base_hp_regen + (vit * 0.002) 
        
        hp_regen = int(character['max_health'] * hp_regen_percent * minutes_passed)
        mp_regen = int(character['max_mana'] * base_mp_regen * minutes_passed)
        # ===========================================
        
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
    if level >= 100: return 'S'
    elif level >= 60: return 'A'
    elif level >= 35: return 'B'
    elif level >= 25: return 'C'
    elif level >= 15: return 'D'
    return 'E'

# --- ОСНОВНЫЕ ФУНКЦИИ ---



def create_character(user_id, username, char_name, race):
    conn = get_connection()
    if not conn: return False
    
    race_data = RACES.get(race, RACES['human'])
    hp = race_data['vitality'] * race_data['health_multiplier']
    mp = race_data['intelligence'] * race_data['mana_multiplier']
    
    p_res = 0.05 if race == 'orc' else 0.0
    m_res = 0.10 if race == 'dwarf' else 0.0
    
    if race == 'elf': m_res = 0.05
    # Вампиры нежить, у них врожденная защита от физики 10%
    if race == 'vampire': p_res = 0.10
    # НОВЫЕ РАСЫ:
    # У Ящеролюда толстая чешуя (12% поглощения физурона со старта)
    if race == 'lizardman': p_res = 0.12 
    # У Жаболюда скользкая кожа и иммунитет к болотной магии
    if race == 'frogman': m_res = 0.10
    # Нежить не чувствует боли (огромный бонус к защите от физ. урона со старта)
    if race == 'undead': p_res = 0.15    
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
            
            leveled_up = False
            while True:
                # ВОТ ЗДЕСЬ БЫЛА ОШИБКА! Теперь формула точно такая же, как в профиле:
                needed = (cur_lvl * (cur_lvl + 1) * 50) // 2 
                
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
    except Exception as e:
        print(f"Add Experience Error: {e}")
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



def get_all_users():
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM player_characters")
            return [r[0] for r in cursor.fetchall()]
    finally:
        conn.close()
        
def remove_item(user_id, item_key, count=1):
    """
    Удаляет указанное количество предметов.
    Если предметов 5, а удаляем 1 -> останется 4.
    Если предметов 1, а удаляем 1 -> предмет удалится полностью.
    """
    conn = get_connection()
    if not conn: return False
    
    try:
        with conn.cursor() as cursor:
            # 1. Ищем, сколько у нас этого предмета сейчас
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            res = cursor.fetchone()
            
            if not res: return False # Предмета вообще нет
            
            item_id, current_qty = res
            
            # 2. Считаем новый остаток
            new_qty = current_qty - count
            
            if new_qty <= 0:
                # Если остаток 0 или меньше — удаляем строку целиком
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
            else:
                # Иначе просто обновляем число
                cursor.execute("UPDATE player_inventory SET quantity = %s WHERE id=%s", (new_qty, item_id))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Remove item error: {e}")
        return False
    finally:
        conn.close()
# --- ДОБАВИТЬ В init_db (внутри CREATE TABLE player_characters) ---
# Если база уже есть, выполните этот SQL в вашей программе управления БД:
# ALTER TABLE player_characters ADD COLUMN quest_target VARCHAR(50);
# ALTER TABLE player_characters ADD COLUMN quest_type VARCHAR(20);
# ALTER TABLE player_characters ADD COLUMN quest_goal INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN quest_progress INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN quest_reward_gold INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN quest_reward_exp INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN last_quest_date DATE;

# --- НОВЫЕ ФУНКЦИИ ДЛЯ КВЕСТОВ (Добавить в database.py) ---

def take_quest(user_id, q_type, target, goal, reward_gold, reward_exp):
    """Берем новое задание"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE player_characters 
                SET quest_type=%s, quest_target=%s, quest_goal=%s, 
                    quest_progress=0, quest_reward_gold=%s, quest_reward_exp=%s
                WHERE user_id=%s
            """, (q_type, target, goal, reward_gold, reward_exp, user_id))
            conn.commit()
            return True
    finally:
        conn.close()

def update_quest_progress(user_id, amount=1):
    """Обновляем прогресс квеста (только для убийств)"""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            # Увеличиваем прогресс, но не больше цели
            cursor.execute("""
                UPDATE player_characters 
                SET quest_progress = LEAST(quest_goal, quest_progress + %s)
                WHERE user_id=%s AND quest_type = 'kill' AND quest_progress < quest_goal
            """, (amount, user_id))
            conn.commit()
    finally:
        conn.close()

def complete_quest(user_id):
    """Завершение квеста с Репутацией и Бонусами"""
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    
    try:
        with conn.cursor() as cursor:
            # Получаем данные квеста и репутацию
            cursor.execute("""
                SELECT quest_reward_gold, quest_reward_exp, quest_type, quest_target, quest_goal, quest_progress, 
                       last_quest_date, quests_completed_today, guild_reputation
                FROM player_characters 
                WHERE user_id=%s
            """, (user_id,))
            
            res = cursor.fetchone()
            if not res or not res[2]: return False, "Нет активного задания."
            
            gold, exp, q_type, target, goal, progress, last_date, daily_count, rep = res
            rep = rep if rep else 0
            
            # --- ПРОВЕРКА ВЫПОЛНЕНИЯ (Как и раньше) ---
            if q_type == 'kill':
                if progress < goal: return False, f"Не выполнено! Убито: {progress}/{goal}"
            elif q_type == 'collect':
                cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, target))
                inv_res = cursor.fetchone()
                current_qty = inv_res[1] if inv_res else 0
                if current_qty < goal: return False, f"Не хватает предметов! ({current_qty}/{goal})"
                # Удаляем предметы
                item_id = inv_res[0]
                if current_qty == goal: cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
                else: cursor.execute("UPDATE player_inventory SET quantity = quantity - %s WHERE id=%s", (goal, item_id))

            # --- ЛОГИКА ДНЕВНОГО ЛИМИТА ---
            today = datetime.now().date()
            if isinstance(last_date, str):
                try: last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                except: pass
            
            new_count = (daily_count + 1) if last_date == today else 1

            # --- ЛОГИКА РЕПУТАЦИИ И БОНУСОВ ---
            new_rep = rep + 10
            bonus_msg = ""
            
            # Шанс на дополнительную награду
            bonus_item = None
            import random
            chance = random.random()
            
            if rep >= 100: # ПОЧЕТ
                if chance < 0.30: # 30% шанс
                    bonus_item = random.choice(['medium_hp', 'iron_ore', 'small_mp'])
            elif rep >= 50: # УВАЖЕНИЕ
                if chance < 0.20: # 20% шанс
                    bonus_item = 'small_hp'
            
            # Выдача бонусного предмета
            if bonus_item:
                # Простейшая вставка в инвентарь (копируем логику buy_item или пишем SQL)
                cursor.execute("SELECT id FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, bonus_item))
                exist = cursor.fetchone()
                if exist:
                    cursor.execute("UPDATE player_inventory SET quantity = quantity + 1 WHERE id=%s", (exist[0],))
                else:
                    # Нам нужно имя и тип предмета, но здесь мы упростим
                    # В идеале нужно подтянуть из ITEMS_DB, но database не видит bot.py
                    # Поэтому запишем "Бонус гильдии" как имя
                    cursor.execute("INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity) VALUES (%s, %s, 'potion', '🎁 Награда Гильдии', 1)", (user_id, bonus_item))
                bonus_msg = "\n🎁 Гильдия выдала вам доп. припасы!"

            # ОБНОВЛЕНИЕ ПЕРСОНАЖА
            cursor.execute("""
                UPDATE player_characters 
                SET gold = gold + %s, 
                    guild_reputation = %s,
                    quest_type = NULL, quest_target = NULL, quest_goal = 0, quest_progress = 0,
                    last_quest_date = CURRENT_DATE,
                    quests_completed_today = %s
                WHERE user_id=%s
            """, (gold, new_rep, new_count, user_id))
            
            conn.commit()
            
            # Начисляем опыт через функцию уровня
            add_experience(user_id, exp)
            
            return True, f"✅ Задание выполнено!\nНаграда: {gold}g и {exp}xp\n🤝 Репутация: {new_rep} (+10){bonus_msg}\n({new_count}/2 за сегодня)"
            
    except Exception as e:
        print(f"Quest Error: {e}")
        return False, f"Сбой: {e}"
    finally:
        conn.close()
        
def get_stored_quests(user_id):
    """Возвращает сохраненные квесты и дату их генерации"""
    conn = get_connection()
    if not conn: return None, None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT daily_quests_data, last_refresh_date FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if res and res[0]:
                return json.loads(res[0]), res[1]
            return None, None
    except Exception as e:
        print(f"Get quests error: {e}")
        return None, None
    finally:
        conn.close()

def save_daily_quests(user_id, quests):
    """Сохраняет список квестов и обновляет дату генерации на сегодня"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            json_data = json.dumps(quests)
            cursor.execute("""
                UPDATE player_characters 
                SET daily_quests_data = %s, last_refresh_date = CURRENT_DATE 
                WHERE user_id = %s
            """, (json_data, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Save quests error: {e}")
        return False
    finally:
        conn.close()
def set_elf_magic(user_id, magic_type):
    """Устанавливает тип магии для эльфа"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET elf_magic_type = %s WHERE user_id = %s", (magic_type, user_id))
            conn.commit()
            return True
    finally:
        conn.close()
def set_elf_spell(user_id, spell_key):
    """Запоминает выбранное активное заклинание"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET elf_active_spell = %s WHERE user_id = %s", (spell_key, user_id))
            conn.commit()
            return True
    finally:
        conn.close()
# --- ВСТАВИТЬ В КОНЕЦ database.py ---
def check_inventory_space(user_id, item_type):
    """Проверяет, есть ли место (Максимум 5 шт. для брони/оружия)"""
    conn = get_connection()
    if not conn: return True # Если ошибка БД, лучше разрешить, чем ломать игру
    try:
        with conn.cursor() as cursor:
            # Считаем предметы этого типа
            cursor.execute("SELECT COUNT(*) FROM player_inventory WHERE user_id = %s AND item_type = %s", (user_id, item_type))
            count = cursor.fetchone()[0]
            
            # Лимиты
            limit = 5
            # Если это оружие или броня - проверяем лимит. Остальное (зелья) - безлимит.
            if item_type in ['weapon', 'armor']:
                return count < limit
            return True
    except Exception as e:
        print(f"DB Error (check_space): {e}")
        return True # В случае ошибки разрешаем крафт
    finally:
        conn.close()


def get_inventory_count(user_id, item_type):
    """Возвращает количество предметов определенного типа (для отображения)"""
    conn = get_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM player_inventory WHERE user_id = %s AND item_type = %s", (user_id, item_type))
            return cursor.fetchone()[0]
    finally:
        conn.close()

def sell_item_transaction(user_id, item_key, quantity=1):
    """
    Продает предмет:
    1. Проверяет наличие.
    2. Снимает статы (если это экипировка).
    3. Удаляет предмет.
    4. Начисляет золото (50% от цены).
    """
    # Здесь нам нужен доступ к ITEMS_DB, но database.py не видит bot.py.
    # Поэтому мы передадим цену и характеристики аргументами из бота,
    # ЛИБО (проще) сделаем всю логику проверок в боте, а здесь только SQL.
    # Но для надежности лучше так:
    pass 
    # СТОП. Чтобы не усложнять импорты, сделаем универсальную функцию изменения,
    # а логику "что отнимать" посчитаем в bot.py.




def cancel_quest(user_id):
    """Отказ от задания (штраф репутации)"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            # Проверяем, есть ли квест
            cursor.execute("SELECT quest_type, guild_reputation FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if not res or not res[0]: return False, "Нет задания."
            
            current_rep = res[1] if res[1] else 0
            new_rep = current_rep - 10
            
            # Сбрасываем квест и отнимаем репутацию
            cursor.execute("""
                UPDATE player_characters 
                SET quest_type = NULL, quest_target = NULL, quest_goal = 0, quest_progress = 0,
                    guild_reputation = %s
                WHERE user_id=%s
            """, (new_rep, user_id))
            
            conn.commit()
            return True, f"Задание отменено.\n📉 Репутация: {new_rep} (-10)"
    finally:
        conn.close()
def check_building(user_id, building_name):
    """Проверяет, построено ли здание"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as c:
            # ИСПРАВЛЕНО: имя таблицы player_inventory
            c.execute("SELECT quantity FROM player_inventory WHERE user_id = %s AND item_key = %s", (user_id, building_name))
            res = c.fetchone()
            return res and res[0] > 0
    finally:
        conn.close()

def build_building(user_id, building_name):
    """Строит здание (выдает невидимый предмет)"""
    conn = get_connection()
    if not conn: return
    
    names = {
        'building_alchemy': 'Лавка Травника',
        'building_farm': 'Ферма',
        'building_kitchen': 'Кухня',
        'building_pier': 'Причал',
        'building_apiary': 'Пасека'
    }
    b_name = names.get(building_name, 'Постройка')
    
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount) 
                VALUES (%s, %s, 'building', %s, 1, 0) 
            """, (user_id, building_name, b_name))
            conn.commit()
    except Exception as e:
        print(f"Build error: {e}")
    finally:
        conn.close()



def init_companion_table():
    """Создает таблицу для экспедиций, если её нет"""
    conn = get_connection()
    if not conn: return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS expeditions (
            user_id BIGINT PRIMARY KEY,
            state TEXT DEFAULT 'idle',
            location TEXT,
            start_time TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
def migrate_expeditions_table():
    """Исправляет тип user_id в таблице expeditions с INTEGER на BIGINT"""
    conn = get_connection()
    if not conn: return
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE expeditions ALTER COLUMN user_id TYPE BIGINT")
        conn.commit()
        print("✅ Таблица expeditions обновлена (BIGINT)")
    except Exception as e:
        print(f"⚠️ Миграция не требуется или ошибка: {e}")
    finally:
        conn.close()
def get_expedition_status(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT state, location, start_time FROM expeditions WHERE user_id = %s", (user_id,))
    res = c.fetchone()
    conn.close()
    if not res:
        return {'state': 'idle', 'location': None, 'start_time': None}
    return {'state': res[0], 'location': res[1], 'start_time': res[2]}

def start_expedition(user_id, location):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now()
    c.execute("""
        INSERT INTO expeditions (user_id, state, location, start_time) 
        VALUES (%s, 'busy', %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET state='busy', location=%s, start_time=%s
    """, (user_id, location, now, location, now))
    conn.commit()
    conn.close()

def finish_expedition(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE expeditions SET state='idle', location=NULL, start_time=NULL WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
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
            # 1. Создание основной таблицы (если нет)
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
            
            # 2. Создание таблицы инвентаря (если нет)
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON player_inventory (user_id, item_key)")

            # --- 3. АВТОМАТИЧЕСКОЕ ДОБАВЛЕНИЕ НОВЫХ КОЛОНОК (МИГРАЦИЯ) ---
            # Мы пытаемся добавить колонки. Если они есть — команда просто игнорируется или падает (мы ловим ошибку).
            # Это "грязный", но простой способ обновить структуру без сложных миграций.
            
            columns_to_add = [
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_target VARCHAR(50)",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_type VARCHAR(20)",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_goal INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_progress INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_reward_gold INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quest_reward_exp INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_quest_date DATE",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS daily_quests_data TEXT",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_refresh_date DATE",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS elf_magic_type VARCHAR(20)",
                # В списке columns_to_add:
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS elf_active_spell VARCHAR(50)",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS quests_completed_today INTEGER DEFAULT 0",
                "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS guild_reputation INTEGER DEFAULT 0"
            ]
            
            for sql in columns_to_add:
                try:
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    # Если колонка уже есть или БД не поддерживает IF NOT EXISTS (старый postgres),
                    # просто откатываем транзакцию и идем дальше
                    conn.rollback() 

            conn.commit()
            print("✅ База данных обновлена (структура проверена).")
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

        vit = character.get('vitality', 10)
        regen_percent = 0.05 + (vit * 0.002) # Базовые 5% + 0.2% за каждую единицу живучести
        hp_regen = int(character['max_health'] * regen_percent * minutes_passed)
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
    """Новая, правильная система рангов (до 150 ур)"""
    if level >= 100: return 'S'
    elif level >= 60: return 'A'
    elif level >= 35: return 'B'
    elif level >= 25: return 'C'
    elif level >= 15: return 'D'
    return 'E'
# --- ОСНОВНЫЕ ФУНКЦИИ ---



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

def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=0, amount=1):
    """Полная функция покупки с выдачей характеристик и поддержкой покупки нескольких штук"""
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    
    try:
        with conn.cursor() as cursor:
            # 1. Проверяем деньги (умножаем на количество)
            total_price = price * amount
            if total_price > 0:
                cursor.execute("SELECT gold FROM player_characters WHERE user_id=%s", (user_id,))
                res = cursor.fetchone()
                if not res or res[0] < total_price:
                    return False, f"Не хватает золота! Нужно {total_price}g"
                cursor.execute("UPDATE player_characters SET gold = gold - %s WHERE user_id=%s", (total_price, user_id))

            # 2. Добавляем в инвентарь (прибавляем amount, а не 1)
            cursor.execute("SELECT id FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            exist = cursor.fetchone()
            if exist:
                cursor.execute("UPDATE player_inventory SET quantity = quantity + %s WHERE id=%s", (amount, exist[0]))
            else:
                cursor.execute("""
                    INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, item_key, item_type, item_name, amount, effect_amount))

            # 3. ПРИМЕНЯЕМ БОНУСЫ (Только если покупается 1 шт, защита для экипировки)
            msg_extra = ""
            if amount == 1:
                if item_type == 'weapon':
                    cursor.execute("UPDATE player_characters SET strength = strength + %s WHERE user_id=%s", (effect_amount, user_id))
                    msg_extra = f"\n💪 Сила +{effect_amount}"
                    
                elif item_type == 'magic_weapon':
                    int_bonus = effect_amount
                    mp_bonus = int_bonus * 3
                    cursor.execute("UPDATE player_characters SET intelligence = intelligence + %s, max_mana = max_mana + %s, mana = mana + %s WHERE user_id=%s", (int_bonus, mp_bonus, mp_bonus, user_id))
                    msg_extra = f"\n🔮 Инт +{int_bonus} / Мана +{mp_bonus}"

                elif item_type == 'agi_weapon':
                    agi_bonus = effect_amount
                    str_bonus = max(1, effect_amount // 2)
                    cursor.execute("""
                        UPDATE player_characters 
                        SET agility = agility + %s, strength = strength + %s 
                        WHERE user_id=%s
                    """, (agi_bonus, str_bonus, user_id))
                    msg_extra = f"\n🗡 Ловк +{agi_bonus} | Сила +{str_bonus}"

                elif item_type == 'heavy_armor':
                    hp_bonus = effect_amount
                    p_res_bonus = effect_amount / 200.0 
                    cursor.execute("""
                        UPDATE player_characters 
                        SET max_health = max_health + %s, health = health + %s, physical_resistance = LEAST(0.75, physical_resistance + %s)
                        WHERE user_id=%s
                    """, (hp_bonus, hp_bonus, p_res_bonus, user_id))
                    msg_extra = f"\n🛡 HP +{hp_bonus} | Физ. защита +{int(p_res_bonus*100)}%"

                elif item_type == 'light_armor':
                    hp_bonus = int(effect_amount * 0.6)
                    agi_bonus = int(effect_amount / 2) 
                    cursor.execute("""
                        UPDATE player_characters 
                        SET max_health = max_health + %s, health = health + %s, agility = agility + %s
                        WHERE user_id=%s
                    """, (hp_bonus, hp_bonus, agi_bonus, user_id))
                    msg_extra = f"\n💨 HP +{hp_bonus} | Ловк +{agi_bonus}"

                elif item_type == 'magic_armor':
                    mp_bonus = effect_amount * 2
                    m_res_bonus = effect_amount / 200.0 
                    cursor.execute("""
                        UPDATE player_characters 
                        SET max_mana = max_mana + %s, mana = mana + %s, magic_resistance = LEAST(0.75, magic_resistance + %s)
                        WHERE user_id=%s
                    """, (mp_bonus, mp_bonus, m_res_bonus, user_id))
                    msg_extra = f"\n🔮 Мана +{mp_bonus} | Маг. защита +{int(m_res_bonus*100)}%"

                elif item_type in ['artifact', 'acc']:
                    int_bonus = effect_amount
                    mp_bonus = int_bonus * 5
                    cursor.execute("UPDATE player_characters SET intelligence = intelligence + %s, max_mana = max_mana + %s, mana = mana + %s WHERE user_id=%s", (int_bonus, mp_bonus, mp_bonus, user_id))
                    msg_extra = f"\n🧠 Инт +{int_bonus}"

            conn.commit()
            
            # Красивый вывод с учетом количества
            if amount > 1:
                action = "Куплено" if price > 0 else "Получено"
                return True, f"✅ {action}: {item_name} (x{amount})"
            else:
                action = "Куплено" if price > 0 else "Получено"
                return True, f"✅ {action}: {item_name}{msg_extra}"

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

# --- ЖЕЛЕЗНАЯ СИСТЕМА УРОВНЕЙ ---
def get_correct_level(exp):
    """Считает, какой уровень должен быть у игрока при его текущем опыте"""
    lvl = 1
    while True:
        needed = (lvl * (lvl + 1) * 50) // 2
        if exp >= needed:
            lvl += 1
        else:
            break
    return lvl

def get_character(user_id):
    conn = get_connection()
    if not conn: return None
    char = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM player_characters WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if not row: return None
            
            # Превращаем в обычный словарь
            char = dict(row)
            
            # --- БЕЗОПАСНАЯ ПРОВЕРКА УРОВНЯ ---
            cur_exp = int(char.get('experience', 0))
            cur_lvl = int(char.get('level', 1))
            pts = int(char.get('stat_points', 0))
            
            correct_lvl = get_correct_level(cur_exp)
            
            # Если опыта хватает на новый уровень:
            if correct_lvl > cur_lvl:
                levels_gained = correct_lvl - cur_lvl
                pts += (levels_gained * 2) # 2 очка за каждый уровень
                
                max_hp = int(char.get('max_health', 64))
                max_mp = int(char.get('max_mana', 24))
                
                cursor.execute("""
                    UPDATE player_characters 
                    SET level=%s, stat_points=%s, health=%s, mana=%s 
                    WHERE user_id=%s
                """, (correct_lvl, pts, max_hp, max_mp, user_id))
                
                # Обновляем данные для отображения в боте
                char['level'] = correct_lvl
                char['stat_points'] = pts
                char['health'] = max_hp
                char['mana'] = max_mp

            # Обновляем активность
            cursor.execute("UPDATE player_characters SET last_active = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
            conn.commit()
            
    except Exception as e:
        print(f"Get character error: {e}")
        return None
    finally:
        if conn: conn.close()

    # --- Эти функции вызываются ПОСЛЕ закрытия БД, чтобы не было зависаний ---
    if char:
        char = apply_regeneration(char)
        actual_rank = calculate_rank(char['level'])
        if char.get('rank') != actual_rank:
            update_character_stats(user_id, rank=actual_rank)
            char['rank'] = actual_rank
            
    return char


def add_experience(user_id, exp_amount):
    """Теперь эта функция ТОЛЬКО добавляет опыт. Уровень проверится сам."""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET experience = experience + %s WHERE user_id=%s", (int(exp_amount), user_id))
            conn.commit()
    except Exception as e:
        print(f"Add Experience Error: {e}")
    finally:
        if conn: conn.close()

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

def get_top_players(limit=10, offset=0):
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT pc.character_name, pc.race, pc.level, pc.boss_kills, cl.name as clan_name 
                FROM player_characters pc
                LEFT JOIN clans cl ON pc.clan_id = cl.id 
                ORDER BY pc.level DESC, pc.experience DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
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
        
def remove_item(user_id, item_key, count=1):
    """
    Удаляет указанное количество предметов.
    Если предметов 5, а удаляем 1 -> останется 4.
    Если предметов 1, а удаляем 1 -> предмет удалится полностью.
    """
    conn = get_connection()
    if not conn: return False
    
    try:
        with conn.cursor() as cursor:
            # 1. Ищем, сколько у нас этого предмета сейчас
            cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, item_key))
            res = cursor.fetchone()
            
            if not res: return False # Предмета вообще нет
            
            item_id, current_qty = res
            
            # 2. Считаем новый остаток
            new_qty = current_qty - count
            
            if new_qty <= 0:
                # Если остаток 0 или меньше — удаляем строку целиком
                cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
            else:
                # Иначе просто обновляем число
                cursor.execute("UPDATE player_inventory SET quantity = %s WHERE id=%s", (new_qty, item_id))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Remove item error: {e}")
        return False
    finally:
        conn.close()
# --- ДОБАВИТЬ В init_db (внутри CREATE TABLE player_characters) ---
# Если база уже есть, выполните этот SQL в вашей программе управления БД:
# ALTER TABLE player_characters ADD COLUMN quest_target VARCHAR(50);
# ALTER TABLE player_characters ADD COLUMN quest_type VARCHAR(20);
# ALTER TABLE player_characters ADD COLUMN quest_goal INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN quest_progress INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN quest_reward_gold INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN quest_reward_exp INTEGER DEFAULT 0;
# ALTER TABLE player_characters ADD COLUMN last_quest_date DATE;

# --- НОВЫЕ ФУНКЦИИ ДЛЯ КВЕСТОВ (Добавить в database.py) ---

def take_quest(user_id, q_type, target, goal, reward_gold, reward_exp):
    """Берем новое задание"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE player_characters 
                SET quest_type=%s, quest_target=%s, quest_goal=%s, 
                    quest_progress=0, quest_reward_gold=%s, quest_reward_exp=%s
                WHERE user_id=%s
            """, (q_type, target, goal, reward_gold, reward_exp, user_id))
            conn.commit()
            return True
    finally:
        conn.close()

def update_quest_progress(user_id, amount=1):
    """Обновляем прогресс квеста (только для убийств)"""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor:
            # Увеличиваем прогресс, но не больше цели
            cursor.execute("""
                UPDATE player_characters 
                SET quest_progress = LEAST(quest_goal, quest_progress + %s)
                WHERE user_id=%s AND quest_type = 'kill' AND quest_progress < quest_goal
            """, (amount, user_id))
            conn.commit()
    finally:
        conn.close()

def complete_quest(user_id):
    """Завершение квеста с Репутацией и Бонусами"""
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    
    try:
        with conn.cursor() as cursor:
            # Получаем данные квеста и репутацию
            cursor.execute("""
                SELECT quest_reward_gold, quest_reward_exp, quest_type, quest_target, quest_goal, quest_progress, 
                       last_quest_date, quests_completed_today, guild_reputation
                FROM player_characters 
                WHERE user_id=%s
            """, (user_id,))
            
            res = cursor.fetchone()
            if not res or not res[2]: return False, "Нет активного задания."
            
            gold, exp, q_type, target, goal, progress, last_date, daily_count, rep = res
            rep = rep if rep else 0
            
            # --- ПРОВЕРКА ВЫПОЛНЕНИЯ (Как и раньше) ---
            if q_type == 'kill':
                if progress < goal: return False, f"Не выполнено! Убито: {progress}/{goal}"
            elif q_type == 'collect':
                cursor.execute("SELECT id, quantity FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, target))
                inv_res = cursor.fetchone()
                current_qty = inv_res[1] if inv_res else 0
                if current_qty < goal: return False, f"Не хватает предметов! ({current_qty}/{goal})"
                # Удаляем предметы
                item_id = inv_res[0]
                if current_qty == goal: cursor.execute("DELETE FROM player_inventory WHERE id=%s", (item_id,))
                else: cursor.execute("UPDATE player_inventory SET quantity = quantity - %s WHERE id=%s", (goal, item_id))

            # --- ЛОГИКА ДНЕВНОГО ЛИМИТА ---
            today = datetime.now().date()
            if isinstance(last_date, str):
                try: last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                except: pass
            
            new_count = (daily_count + 1) if last_date == today else 1

            # --- ЛОГИКА РЕПУТАЦИИ И БОНУСОВ ---
            new_rep = rep + 10
            bonus_msg = ""
            
            # Шанс на дополнительную награду
            bonus_item = None
            import random
            chance = random.random()
            
            if rep >= 100: # ПОЧЕТ
                if chance < 0.30: # 30% шанс
                    bonus_item = random.choice(['medium_hp', 'iron_ore', 'small_mp'])
            elif rep >= 50: # УВАЖЕНИЕ
                if chance < 0.20: # 20% шанс
                    bonus_item = 'small_hp'
            
            # Выдача бонусного предмета
            if bonus_item:
                # Простейшая вставка в инвентарь (копируем логику buy_item или пишем SQL)
                cursor.execute("SELECT id FROM player_inventory WHERE user_id=%s AND item_key=%s", (user_id, bonus_item))
                exist = cursor.fetchone()
                if exist:
                    cursor.execute("UPDATE player_inventory SET quantity = quantity + 1 WHERE id=%s", (exist[0],))
                else:
                    # Нам нужно имя и тип предмета, но здесь мы упростим
                    # В идеале нужно подтянуть из ITEMS_DB, но database не видит bot.py
                    # Поэтому запишем "Бонус гильдии" как имя
                    cursor.execute("INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity) VALUES (%s, %s, 'potion', '🎁 Награда Гильдии', 1)", (user_id, bonus_item))
                bonus_msg = "\n🎁 Гильдия выдала вам доп. припасы!"

            # ОБНОВЛЕНИЕ ПЕРСОНАЖА
            cursor.execute("""
                UPDATE player_characters 
                SET gold = gold + %s, 
                    guild_reputation = %s,
                    quest_type = NULL, quest_target = NULL, quest_goal = 0, quest_progress = 0,
                    last_quest_date = CURRENT_DATE,
                    quests_completed_today = %s
                WHERE user_id=%s
            """, (gold, new_rep, new_count, user_id))
            
            conn.commit()
            
            # Начисляем опыт через функцию уровня
            add_experience(user_id, exp)
            
            return True, f"✅ Задание выполнено!\nНаграда: {gold}g и {exp}xp\n🤝 Репутация: {new_rep} (+10){bonus_msg}\n({new_count}/2 за сегодня)"
            
    except Exception as e:
        print(f"Quest Error: {e}")
        return False, f"Сбой: {e}"
    finally:
        conn.close()
        
def get_stored_quests(user_id):
    """Возвращает сохраненные квесты и дату их генерации"""
    conn = get_connection()
    if not conn: return None, None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT daily_quests_data, last_refresh_date FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if res and res[0]:
                return json.loads(res[0]), res[1]
            return None, None
    except Exception as e:
        print(f"Get quests error: {e}")
        return None, None
    finally:
        conn.close()

def save_daily_quests(user_id, quests):
    """Сохраняет список квестов и обновляет дату генерации на сегодня"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            json_data = json.dumps(quests)
            cursor.execute("""
                UPDATE player_characters 
                SET daily_quests_data = %s, last_refresh_date = CURRENT_DATE 
                WHERE user_id = %s
            """, (json_data, user_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Save quests error: {e}")
        return False
    finally:
        conn.close()
def set_elf_magic(user_id, magic_type):
    """Устанавливает тип магии для эльфа"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET elf_magic_type = %s WHERE user_id = %s", (magic_type, user_id))
            conn.commit()
            return True
    finally:
        conn.close()
def set_elf_spell(user_id, spell_key):
    """Запоминает выбранное активное заклинание"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE player_characters SET elf_active_spell = %s WHERE user_id = %s", (spell_key, user_id))
            conn.commit()
            return True
    finally:
        conn.close()
# --- ВСТАВИТЬ В КОНЕЦ database.py ---
def check_inventory_space(user_id, item_type):
    """Проверяет, есть ли место (Максимум 5 шт. для брони/оружия)"""
    conn = get_connection()
    if not conn: return True # Если ошибка БД, лучше разрешить, чем ломать игру
    try:
        with conn.cursor() as cursor:
            # Считаем предметы этого типа
            cursor.execute("SELECT COUNT(*) FROM player_inventory WHERE user_id = %s AND item_type = %s", (user_id, item_type))
            count = cursor.fetchone()[0]
            
            # Лимиты
            limit = 5
            # Если это оружие или броня - проверяем лимит. Остальное (зелья) - безлимит.
            if item_type in ['weapon', 'armor']:
                return count < limit
            return True
    except Exception as e:
        print(f"DB Error (check_space): {e}")
        return True # В случае ошибки разрешаем крафт
    finally:
        conn.close()


def get_inventory_count(user_id, item_type):
    """Возвращает количество предметов определенного типа (для отображения)"""
    conn = get_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM player_inventory WHERE user_id = %s AND item_type = %s", (user_id, item_type))
            return cursor.fetchone()[0]
    finally:
        conn.close()

def execute_sell(user_id, item_key, price_to_add, stat_changes=None):
    """
    Единственная и безопасная функция продажи с абсолютной защитой от минусовых статов.
    """
    conn = get_connection()
    if not conn: return False, "Ошибка подключения"
    
    try:
        with conn.cursor() as cursor:
            # 1. Жесткое списание (только если предмет реально есть)
            cursor.execute("""
                UPDATE player_inventory 
                SET quantity = quantity - 1 
                WHERE user_id = %s AND item_key = %s AND quantity >= 1
            """, (user_id, item_key))
            
            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Предмет не найден или уже продан!"
            
            # 2. Очистка пустых слотов
            cursor.execute("DELETE FROM player_inventory WHERE user_id = %s AND quantity <= 0", (user_id,))
            
            # 3. Начисление золота
            cursor.execute("UPDATE player_characters SET gold = gold + %s WHERE user_id = %s", (price_to_add, user_id))
            
            # 4. Снятие статов с защитой от ухода в минус
            if stat_changes:
                for stat_name, change_val in stat_changes.items():
                    # Резисты не падают ниже 0.0, остальные статы не ниже 1
                    min_val = 0.0 if 'resistance' in stat_name else 1
                    
                    sql = f"""
                        UPDATE player_characters 
                        SET {stat_name} = GREATEST(%s, {stat_name} + %s) 
                        WHERE user_id = %s
                    """
                    cursor.execute(sql, (min_val, change_val, user_id))
            
            conn.commit()
            return True, "Успешно"
    except Exception as e:
        conn.rollback()
        print(f"Sell error: {e}")
        return False, f"Ошибка: {e}"
    finally:
        conn.close()
        

def cancel_quest(user_id):
    """Отказ от задания (штраф репутации)"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            # Проверяем, есть ли квест
            cursor.execute("SELECT quest_type, guild_reputation FROM player_characters WHERE user_id=%s", (user_id,))
            res = cursor.fetchone()
            if not res or not res[0]: return False, "Нет задания."
            
            current_rep = res[1] if res[1] else 0
            new_rep = current_rep - 10
            
            # Сбрасываем квест и отнимаем репутацию
            cursor.execute("""
                UPDATE player_characters 
                SET quest_type = NULL, quest_target = NULL, quest_goal = 0, quest_progress = 0,
                    guild_reputation = %s
                WHERE user_id=%s
            """, (new_rep, user_id))
            
            conn.commit()
            return True, f"Задание отменено.\n📉 Репутация: {new_rep} (-10)"
    finally:
        conn.close()
def check_building(user_id, building_name):
    """Проверяет, построено ли здание"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as c:
            # ИСПРАВЛЕНО: имя таблицы player_inventory
            c.execute("SELECT quantity FROM player_inventory WHERE user_id = %s AND item_key = %s", (user_id, building_name))
            res = c.fetchone()
            return res and res[0] > 0
    finally:
        conn.close()

def build_building(user_id, building_name):
    """Строит здание (выдает невидимый предмет)"""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as c:
            # ИСПРАВЛЕНО: 
            # 1. Имя таблицы player_inventory
            # 2. Убрана колонка equip_slot (её нет в базе)
            # 3. Добавлен effect_amount = 0
            c.execute("""
                INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity, effect_amount) 
                VALUES (%s, %s, 'building', 'Лавка Травника', 1, 0) 
            """, (user_id, building_name))
            conn.commit()
    except Exception as e:
        print(f"Build error: {e}")
    finally:
        conn.close()

def init_companion_table():
    """Создает таблицу для экспедиций, если её нет"""
    conn = get_connection()
    if not conn: return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS expeditions (
            user_id BIGINT PRIMARY KEY,
            state TEXT DEFAULT 'idle',
            location TEXT,
            start_time TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_expedition_status(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT state, location, start_time FROM expeditions WHERE user_id = %s", (user_id,))
    res = c.fetchone()
    conn.close()
    if not res:
        return {'state': 'idle', 'location': None, 'start_time': None}
    return {'state': res[0], 'location': res[1], 'start_time': res[2]}

def start_expedition(user_id, location):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now()
    c.execute("""
        INSERT INTO expeditions (user_id, state, location, start_time) 
        VALUES (%s, 'busy', %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET state='busy', location=%s, start_time=%s
    """, (user_id, location, now, location, now))
    conn.commit()
    conn.close()

def finish_expedition(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE expeditions SET state='idle', location=NULL, start_time=NULL WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()
# --- МЕХАНИКА ФЕРМЕРА ---
def init_farm_table():
    """Создает таблицу для Фермы"""
    conn = get_connection()
    if not conn: return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS farm_jobs (
            user_id BIGINT PRIMARY KEY,
            state TEXT DEFAULT 'idle',
            crop_key TEXT,
            start_time TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_farm_status(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT state, crop_key, start_time FROM farm_jobs WHERE user_id = %s", (user_id,))
    res = c.fetchone()
    conn.close()
    if not res:
        return {'state': 'idle', 'crop_key': None, 'start_time': None}
    return {'state': res[0], 'crop_key': res[1], 'start_time': res[2]}

def start_farming(user_id, crop_key):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now()
    c.execute("""
        INSERT INTO farm_jobs (user_id, state, crop_key, start_time) 
        VALUES (%s, 'growing', %s, %s)
        ON CONFLICT(user_id) DO UPDATE SET state='growing', crop_key=%s, start_time=%s
    """, (user_id, crop_key, now, crop_key, now))
    conn.commit()
    conn.close()

def finish_farming(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE farm_jobs SET state='idle', crop_key=NULL, start_time=NULL WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()
def delete_character(user_id):
    """Полностью удаляет персонажа и весь его прогресс (Реинкарнация)"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as c:
            # Сначала удаляем все связанные данные (инвентарь, здания, квесты)
            c.execute("DELETE FROM player_inventory WHERE user_id = %s", (user_id,))
            c.execute("DELETE FROM expeditions WHERE user_id = %s", (user_id,))
            c.execute("DELETE FROM farm_jobs WHERE user_id = %s", (user_id,))
            # Затем удаляем самого героя
            c.execute("DELETE FROM player_characters WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Delete character error: {e}")
        return False
    finally:
        conn.close()
# ==========================================
# === СИСТЕМА КЛАНОВ ===
# ==========================================

def init_clans_table():
    """Создает таблицы для кланов и добавляет колонку в профили"""
    conn = get_connection()
    if not conn: return
    try:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS clans (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(30) NOT NULL UNIQUE,
                    owner_id BIGINT NOT NULL,
                    icon_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raid_level INTEGER DEFAULT 1,
                    raid_hp INTEGER DEFAULT 0,
                    raid_max_hp INTEGER DEFAULT 0,
                    raid_points INTEGER DEFAULT 0
                )
            """)
            conn.commit()

        # Разделяем каждую колонку в отдельный блок try...except, 
        # чтобы ошибка в одной не мешала добавиться остальным!
        columns_to_add = [
            "ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS clan_id INTEGER DEFAULT NULL",
            "ALTER TABLE clans ADD COLUMN IF NOT EXISTS raid_level INTEGER DEFAULT 1",
            "ALTER TABLE clans ADD COLUMN IF NOT EXISTS raid_hp INTEGER DEFAULT 0",
            "ALTER TABLE clans ADD COLUMN IF NOT EXISTS raid_max_hp INTEGER DEFAULT 0",
            "ALTER TABLE clans ADD COLUMN IF NOT EXISTS raid_points INTEGER DEFAULT 0"
        ]
        
        for sql in columns_to_add:
            try:
                with conn.cursor() as c:
                    c.execute(sql)
                    conn.commit()
            except Exception:
                conn.rollback() # Игнорируем, если колонка уже есть

        print("✅ Система кланов (и рейдов) инициализирована.")
    except Exception as e:
        print(f"Clan init error: {e}")
    finally:
        conn.close()



def create_clan(user_id, name, icon_id):
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    try:
        with conn.cursor() as c:
            # Списываем 10000 золота
            c.execute("UPDATE player_characters SET gold = gold - 10000 WHERE user_id = %s AND gold >= 10000", (user_id,))
            if c.rowcount == 0:
                return False, "Не хватает золота!"
            
            # Создаем клан
            c.execute("INSERT INTO clans (name, owner_id, icon_id) VALUES (%s, %s, %s) RETURNING id", (name, user_id, icon_id))
            clan_id = c.fetchone()[0]
            
            # Присваиваем клан создателю
            c.execute("UPDATE player_characters SET clan_id = %s WHERE user_id = %s", (clan_id, user_id))
            conn.commit()
            return True, "Клан успешно основан!"
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "Клан с таким названием уже существует!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_clan_by_id(clan_id):
    conn = get_connection()
    if not clan_id: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute("SELECT * FROM clans WHERE id = %s", (clan_id,))
            return c.fetchone()
    finally:
        conn.close()

def get_all_clans():
    conn = get_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            # Сортируем сначала по очкам рейда, потом по количеству участников
            c.execute("""
                SELECT cl.*, COUNT(pc.id) as members_count, owner_pc.character_name as owner_name 
                FROM clans cl 
                LEFT JOIN player_characters pc ON pc.clan_id = cl.id 
                LEFT JOIN player_characters owner_pc ON cl.owner_id = owner_pc.user_id
                GROUP BY cl.id, owner_pc.character_name
                ORDER BY raid_points DESC, members_count DESC 
                LIMIT 20
            """)
            return c.fetchall()
    finally:
        conn.close()

def get_clan_members(clan_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as c:
            c.execute("SELECT character_name, level, rank, user_id FROM player_characters WHERE clan_id = %s ORDER BY level DESC", (clan_id,))
            return c.fetchall()
    finally:
        conn.close()

def join_clan(user_id, clan_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE player_characters SET clan_id = %s WHERE user_id = %s", (clan_id, user_id))
            conn.commit()
    finally:
        conn.close()

def leave_clan(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # Проверяем, не является ли игрок владельцем
            c.execute("SELECT id FROM clans WHERE owner_id = %s", (user_id,))
            owned_clan = c.fetchone()
            
            if owned_clan:
                # Если владелец уходит, клан распускается (всех кикает)
                c.execute("UPDATE player_characters SET clan_id = NULL WHERE clan_id = %s", (owned_clan[0],))
                c.execute("DELETE FROM clans WHERE id = %s", (owned_clan[0],))
            else:
                # Иначе просто убираем игрока
                c.execute("UPDATE player_characters SET clan_id = NULL WHERE user_id = %s", (user_id,))
            conn.commit()
    finally:
        conn.close()
def transfer_gold(sender_id, target_id, amount):
    conn = get_connection()
    if not conn: return False, "БД недоступна"
    try:
        with conn.cursor() as c:
            # Списываем у отправителя (только если хватает денег)
            c.execute("UPDATE player_characters SET gold = gold - %s WHERE user_id = %s AND gold >= %s", (amount, sender_id, amount))
            if c.rowcount == 0: return False, "Недостаточно золота!"
            
            # Начисляем получателю
            c.execute("UPDATE player_characters SET gold = gold + %s WHERE user_id = %s", (amount, target_id))
            conn.commit()
            return True, ""
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def transfer_item(sender_id, target_id, item_key, amount, item_info):
    conn = get_connection()
    if not conn: return False, "БД недоступна"
    try:
        with conn.cursor() as c:
            # Списываем предмет (только если хватает количества)
            c.execute("UPDATE player_inventory SET quantity = quantity - %s WHERE user_id = %s AND item_key = %s AND quantity >= %s", (amount, sender_id, item_key, amount))
            if c.rowcount == 0: return False, "Недостаточно предметов!"
            
            # Удаляем строку, если предметов стало 0
            c.execute("DELETE FROM player_inventory WHERE user_id = %s AND quantity <= 0", (sender_id,))

            # Проверяем, есть ли такой предмет у получателя
            c.execute("SELECT quantity FROM player_inventory WHERE user_id = %s AND item_key = %s", (target_id, item_key))
            res = c.fetchone()
            if res:
                c.execute("UPDATE player_inventory SET quantity = quantity + %s WHERE user_id = %s AND item_key = %s", (amount, target_id, item_key))
            else:
                # ИСПРАВЛЕНИЕ: Убрали item_effect, так как он не хранится в таблице инвентаря
                c.execute("INSERT INTO player_inventory (user_id, item_key, item_type, item_name, quantity) VALUES (%s, %s, %s, %s, %s)",
                          (target_id, item_key, item_info['type'], item_info['name'], amount))
            conn.commit()
            return True, ""
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
def get_honey_collection_time(user_id):
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor() as c:
            c.execute("SELECT last_honey_collection FROM player_characters WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            return res[0] if res else None
    except Exception as e:
        print(f"Honey GET error: {e}")
        # ЭКСТРЕННАЯ МИГРАЦИЯ: Если колонки нет, создаем её прямо сейчас
        try:
            conn.rollback()
            with conn.cursor() as c2:
                c2.execute("ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_honey_collection TIMESTAMP")
                conn.commit()
        except:
            pass
        return None
    finally:
        conn.close()

def update_honey_collection_time(user_id):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as c:
            c.execute("UPDATE player_characters SET last_honey_collection = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Honey UPDATE error: {e}")
        return False
    finally:
        conn.close()
def get_raid_attack_time(user_id):
    conn = get_connection()
    if not conn: return None
    try:
        with conn.cursor() as c:
            c.execute("SELECT last_raid_attack FROM player_characters WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            return res[0] if res else None
    except Exception as e:
        print(f"Raid GET error: {e}")
        # ЭКСТРЕННАЯ МИГРАЦИЯ: Если колонки нет, создаем её на лету
        try:
            conn.rollback()
            with conn.cursor() as c2:
                c2.execute("ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_raid_attack TIMESTAMP")
                conn.commit()
        except:
            pass
        return None
    finally:
        conn.close()

def update_raid_attack_time(user_id):
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as c:
            c.execute("UPDATE player_characters SET last_raid_attack = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Raid UPDATE error: {e}")
        # Если ошибка при записи, пытаемся создать колонку и записать снова
        try:
            conn.rollback()
            with conn.cursor() as c2:
                c2.execute("ALTER TABLE player_characters ADD COLUMN IF NOT EXISTS last_raid_attack TIMESTAMP")
                c2.execute("UPDATE player_characters SET last_raid_attack = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
                conn.commit()
                return True
        except:
            return False
    finally:
        conn.close()

def execute_raid_damage(clan_id, damage):
    """Атомарно вычитает HP босса и возвращает (убит ли босс, оставшееся HP)"""
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE clans SET raid_hp = GREATEST(0, raid_hp - %s) WHERE id = %s RETURNING raid_hp", (damage, clan_id))
            left_hp = c.fetchone()[0]
            
            is_dead = left_hp <= 0
            if is_dead:
                # Если убили, даем очки клану и сбрасываем босса для следующего призыва
                c.execute("UPDATE clans SET raid_points = raid_points + (raid_level * 10), raid_level = raid_level + 1, raid_hp = 0, raid_max_hp = 0 WHERE id = %s", (clan_id,))
            conn.commit()
            return is_dead, left_hp
    finally:
        conn.close()
        
def summon_raid_boss(clan_id, max_hp):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE clans SET raid_hp = %s, raid_max_hp = %s WHERE id = %s", (max_hp, max_hp, clan_id))
            conn.commit()
    finally:
        conn.close()
def change_race(user_id, new_race, cost):
    """Списывает золото и меняет расу персонажа, оставляя статы прежними"""
    conn = get_connection()
    if not conn: return False, "Ошибка БД"
    try:
        with conn.cursor() as c:
            # 1. Проверяем золото и текущую расу
            c.execute("SELECT gold, race FROM player_characters WHERE user_id = %s", (user_id,))
            res = c.fetchone()
            if not res: return False, "Герой не найден"
            if res[0] < cost: return False, "Не хватает золота!"
            if res[1] == new_race: return False, "Вы уже принадлежите к этой расе!"

            # 2. Обновляем расу и списываем золото
            c.execute("UPDATE player_characters SET race = %s, gold = gold - %s WHERE user_id = %s", (new_race, cost, user_id))
            
            # 3. Если игрок ПЕРЕСТАЕТ быть эльфом, очищаем его магию
            if res[1] == 'elf' and new_race != 'elf':
                c.execute("UPDATE player_characters SET elf_active_spell = NULL, elf_magic_type = NULL WHERE user_id = %s", (user_id,))
            
            conn.commit()
            return True, "Ритуал прошел успешно!"
    except Exception as e:
        print(f"Change race error: {e}")
        return False, str(e)
    finally:
        conn.close()
