import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Константы рас
RACES = {
    "human": {
        "name": "Человек", "strength": 10, "agility": 10, "intelligence": 10,
        "health": 100, "mana": 50, "racial_ability": "Адаптивность: +1 ко всем характеристикам"
    },
    "elf": {
        "name": "Эльф", "strength": 8, "agility": 14, "intelligence": 12,
        "health": 80, "mana": 100, "racial_ability": "Магический дар: +50% к мане"
    },
    "dwarf": {
        "name": "Дварф", "strength": 14, "agility": 8, "intelligence": 9,
        "health": 120, "mana": 30, "racial_ability": "Каменная кожа: +20% к здоровью"
    },
    "orc": {
        "name": "Орк", "strength": 16, "agility": 9, "intelligence": 6,
        "health": 110, "mana": 20, "racial_ability": "Ярость: двойной урон при лоу-хп"
    }
}

def get_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        db_host = os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('PGPORT', '5432')
        db_name = os.getenv('PGDATABASE', 'railway')
        db_user = os.getenv('PGUSER', 'postgres')
        db_password = os.getenv('PGPASSWORD', '')
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        # 'prefer' позволяет работать и с SSL (облако), и без (локально)
        return psycopg2.connect(database_url, sslmode='prefer')
    except Exception as e:
        print(f"❌ Критическая ошибка БД: {e}")
        return None

# --- ИНИЦИАЛИЗАЦИЯ ---

def init_db():
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        
        # 1. Персонажи
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_characters (
                user_id BIGINT PRIMARY KEY,
                character_name VARCHAR(100) NOT NULL,
                race VARCHAR(50) NOT NULL,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                strength INTEGER, agility INTEGER, intelligence INTEGER,
                health INTEGER, max_health INTEGER,
                mana INTEGER, max_mana INTEGER,
                gold INTEGER DEFAULT 100,
                battle_wins INTEGER DEFAULT 0,
                battle_losses INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Справочник предметов (Магазин)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(50), -- 'weapon', 'armor', 'consumable'
                price INTEGER NOT NULL,
                bonus_str INTEGER DEFAULT 0,
                bonus_agi INTEGER DEFAULT 0,
                bonus_int INTEGER DEFAULT 0,
                description TEXT
            );
        """)

        # 3. Инвентарь
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES player_characters(user_id) ON DELETE CASCADE,
                item_id INTEGER REFERENCES items(id),
                is_equipped BOOLEAN DEFAULT FALSE,
                quantity INTEGER DEFAULT 1
            );
        """)

        # 4. Логи боев
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                enemy_type VARCHAR(100),
                result VARCHAR(50),
                gold_earned INTEGER DEFAULT 0,
                exp_earned INTEGER DEFAULT 0,
                battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("✅ Система БД успешно развернута")
    finally:
        conn.close()

# --- ЛОГИКА ПЕРСОНАЖА ---

def create_character(user_id, character_name, race):
    if race not in RACES: return False, "Раса не существует"
    r = RACES[race]
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO player_characters 
            (user_id, character_name, race, strength, agility, intelligence, health, max_health, mana, max_mana)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, character_name, race, r['strength'], r['agility'], r['intelligence'], r['health'], r['health'], r['mana'], r['mana']))
        conn.commit()
        return (True, "Персонаж создан!") if cursor.rowcount > 0 else (False, "У вас уже есть герой")
    finally:
        conn.close()

def get_character(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # Получаем статы + суммируем бонусы от экипированных вещей
        cursor.execute("""
            SELECT p.*, 
            COALESCE(SUM(i.bonus_str), 0) as equip_str,
            COALESCE(SUM(i.bonus_agi), 0) as equip_agi
            FROM player_characters p
            LEFT JOIN inventory inv ON p.user_id = inv.user_id AND inv.is_equipped = TRUE
            LEFT JOIN items i ON inv.item_id = i.id
            WHERE p.user_id = %s
            GROUP BY p.user_id
        """, (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()

# --- МАГАЗИН И ИНВЕНТАРЬ ---

def buy_item(user_id, item_id):
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        cursor.execute("SELECT gold FROM player_characters WHERE user_id = %s", (user_id,))
        player = cursor.fetchone()

        if not item or not player: return False, "Данные не найдены"
        if player['gold'] < item['price']: return False, "Недостаточно золота"

        cursor.execute("UPDATE player_characters SET gold = gold - %s WHERE user_id = %s", (item['price'], user_id))
        cursor.execute("INSERT INTO inventory (user_id, item_id) VALUES (%s, %s)", (user_id, item_id))
        conn.commit()
        return True, f"Вы купили {item['name']}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def equip_item(user_id, inventory_id):
    """Надеть предмет из инвентаря"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Снимаем всё того же типа (например, нельзя два меча, если это не предусмотрено)
        # Для простоты: просто переключаем конкретный предмет
        cursor.execute("UPDATE inventory SET is_equipped = NOT is_equipped WHERE id = %s AND user_id = %s", (inventory_id, user_id))
        conn.commit()
        return True
    finally:
        conn.close()

# --- СТАТИСТИКА И ОПЫТ ---

def add_experience(user_id, amount):
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT experience, level, max_health FROM player_characters WHERE user_id = %s", (user_id,))
        res = cursor.fetchone()
        if not res: return False
        
        new_exp = res['experience'] + amount
        new_lvl = res['level']
        lvl_up = False
        
        if new_exp >= (new_lvl * 100):
            new_lvl += 1
            lvl_up = True
            cursor.execute("""
                UPDATE player_characters SET 
                level = %s, experience = %s, 
                strength = strength + 2, max_health = max_health + 20, health = max_health + 20
                WHERE user_id = %s
            """, (new_lvl, new_exp, user_id))
        else:
            cursor.execute("UPDATE player_characters SET experience = %s WHERE user_id = %s", (new_exp, user_id))
        
        conn.commit()
        return True, lvl_up, new_lvl
    finally:
        conn.close()
