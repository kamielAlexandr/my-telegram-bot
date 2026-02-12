import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- КОНСТАНТЫ БАЗЫ ДАННЫХ ---
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
        # Фоллбэк для локальной разработки, если переменная не задана
        return None
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"⚠️ Ошибка подключения с sslmode: {e}")
        try:
            conn = psycopg2.connect(database_url)
            return conn
        except Exception as e2:
            print(f"❌ Не удалось подключиться к БД: {e2}")
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
            
            # Таблица логов боев
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
    except Exception as e:
        print(f"❌ Ошибка init_db: {e}")
    finally:
        conn.close()

def apply_regeneration(character):
    """
    Система регенерации:
    Восстанавливает 5% HP и 5% Mana каждую минуту простоя.
    """
    if not character: return None

    last_regen = character.get('last_regeneration')
    if not last_regen: return character

    now = datetime.now()
    # Разница во времени
    time_diff = now - last_regen
    minutes_passed = int(time_diff.total_seconds() // 60) # Полных минут прошло

    # Если прошло меньше минуты, регенерации нет
    if minutes_passed < 1:
        return character

    max_hp = character['max_health']
    max_mana = character['max_mana']
    current_hp = character['health']
    current_mana = character['mana']

    # Если всё полное, просто обновляем метку времени
    if current_hp >= max_hp and current_mana >= max_mana:
        update_regeneration_timestamp(character['user_id'])
        return character

    # Расчет восстановления (5% в минуту + бонусы от характеристик)
    hp_regen_amount = int((max_hp * 0.05) * minutes_passed)
    mana_regen_amount = int((max_mana * 0.05) * minutes_passed)

    # Применяем восстановление
    new_hp = min(max_hp, current_hp + hp_regen_amount)
    new_mana = min(max_mana, current_mana + mana_regen_amount)

    # Обновляем БД только если значения изменились
    if new_hp != current_hp or new_mana != current_mana:
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
                    
                    # Обновляем локальный объект
                    character['health'] = new_hp
                    character['mana'] = new_mana
                    character['last_regeneration'] = now
            finally:
                conn.close()
    else:
        # Просто обновляем таймер, чтобы не пересчитывать старое время
        update_regeneration_timestamp(character['user_id'])

    return character

def update_regeneration_timestamp(user_id):
    """Обновляет время последней регенерации на текущее"""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE player_characters SET last_regeneration = CURRENT_TIMESTAMP 
                    WHERE user_id = %s
                """, (user_id,))
                conn.commit()
        finally:
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
                # Рассчитываем ранг если его нет
                if not character.get('rank'):
                    rank = 'E' # Логика ранга простая для заглушки
                    if character['level'] >= 10: rank = 'D'
                    if character['level'] >= 20: rank = 'C'
                    if character['level'] >= 30: rank = 'B'
                    if character['level'] >= 40: rank = 'A'
                    if character['level'] >= 50: rank = 'S'
                    character['rank'] = rank
                
                # ПРИМЕНЯЕМ РЕГЕНЕРАЦИЮ ПЕРЕД ВОЗВРАТОМ
                character = apply_regeneration(character)
                
            return character
    finally:
        conn.close()

def create_new_character_db(user_id, name, race):
    conn = get_connection()
    if not conn: return False, "DB Error"
    
    race_data = RACES.get(race)
    if not race_data: return False, "Invalid Race"

    # Расчет статов
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
                 health, max_health, mana, max_mana, physical_resistance, magic_resistance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, race, 
                  race_data['strength'], race_data['agility'], race_data['intelligence'], race_data['vitality'],
                  hp, hp, mana, mana, phys_res, magic_res))
            conn.commit()
            return True, "Success"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# Остальные функции DB (inventory, shop, stats) аналогичны вашим, 
# но обязательно должны использовать get_connection()
