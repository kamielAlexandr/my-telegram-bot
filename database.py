import sqlite3
from datetime import datetime

DB_NAME = "rpg_bot.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица персонажей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        character_name TEXT,
        race TEXT,
        level INTEGER DEFAULT 1,
        experience INTEGER DEFAULT 0,
        health INTEGER,
        max_health INTEGER,
        mana INTEGER,
        max_mana INTEGER,
        strength INTEGER,
        agility INTEGER,
        intelligence INTEGER,
        equip_str INTEGER DEFAULT 0,
        equip_def INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 100,
        battle_wins INTEGER DEFAULT 0,
        battle_losses INTEGER DEFAULT 0,
        last_active DATETIME,
        created_at DATETIME
    )''')

    # Таблица предметов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT, 
        price INTEGER,
        bonus_str INTEGER DEFAULT 0,
        bonus_def INTEGER DEFAULT 0,
        description TEXT
    )''')

    # Таблица инвентаря
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        is_equipped BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES characters(user_id)
    )''')

    # Наполнение магазина
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        items = [
            ('Стальной меч', 'weapon', 50, 5, 0, 'Сила +5'),
            ('Кожаная броня', 'armor', 40, 0, 3, 'Защита +3'),
            ('Зелье жизни', 'potion', 20, 0, 0, 'Восстанавливает 50 HP'),
            ('Топор Гнома', 'weapon', 120, 12, 0, 'Сила +12')
        ]
        cursor.executemany("INSERT INTO items (name, type, price, bonus_str, bonus_def, description) VALUES (?,?,?,?,?,?)", items)

    conn.commit()
    conn.close()

def get_character(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_character(user_id, char_name, race):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    races = {
        'human': (100, 20, 10, 10, 10),
        'elf': (80, 50, 8, 15, 12),
        'dwarf': (130, 10, 12, 8, 5),
        'orc': (110, 10, 15, 7, 3)
    }
    stats = races.get(race, races['human'])
    try:
        cursor.execute('''INSERT INTO characters 
            (user_id, character_name, race, health, max_health, mana, max_mana, strength, agility, intelligence, last_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, char_name, race, stats[0], stats[0], stats[1], stats[1], stats[2], stats[3], stats[4], datetime.now(), datetime.now()))
        conn.commit()
        return True, "Успех"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_character_stats(user_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [user_id]
    cursor.execute(f"UPDATE characters SET {fields} WHERE user_id = ?", values)
    conn.commit()
    conn.close()

def add_experience(user_id, exp):
    char = get_character(user_id)
    new_exp = char['experience'] + exp
    new_lvl = char['level']
    if new_exp >= char['level'] * 100:
        new_lvl += 1
        new_exp -= char['level'] * 100
        # При лвлапе даем бонус к статам
        update_character_stats(user_id, level=new_lvl, experience=new_exp, 
                               strength=char['strength']+2, max_health=char['max_health']+20, health=char['max_health']+20)
        return True # Level Up!
    update_character_stats(user_id, experience=new_exp)
    return False

def get_inventory(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''SELECT i.id, it.name, it.type, it.bonus_str, it.bonus_def, i.is_equipped 
                      FROM inventory i JOIN items it ON i.item_id = it.id WHERE i.user_id = ?''', (user_id,))
    res = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return res

def buy_item(user_id, item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT gold FROM characters WHERE user_id = ?", (user_id,))
    gold = cursor.fetchone()[0]
    cursor.execute("SELECT price, name FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if gold >= item[0]:
        cursor.execute("UPDATE characters SET gold = gold - ? WHERE user_id = ?", (item[0], user_id))
        cursor.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
        conn.commit()
        conn.close()
        return True, f"Куплено: {item[1]}"
    conn.close()
    return False, "Мало золота!"

def equip_item(user_id, inv_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT it.type, i.is_equipped FROM inventory i JOIN items it ON i.item_id = it.id WHERE i.id = ?", (inv_id,))
    item_type, is_eq = cursor.fetchone()
    if is_eq:
        cursor.execute("UPDATE inventory SET is_equipped = 0 WHERE id = ?", (inv_id,))
    else:
        cursor.execute("UPDATE inventory SET is_equipped = 0 WHERE user_id = ? AND item_id IN (SELECT id FROM items WHERE type = ?)", (user_id, item_type))
        cursor.execute("UPDATE inventory SET is_equipped = 1 WHERE id = ?", (inv_id,))
    conn.commit()
    conn.close()
    recalculate_stats(user_id)

def recalculate_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(it.bonus_str), SUM(it.bonus_def) FROM inventory i JOIN items it ON i.item_id = it.id WHERE i.user_id = ? AND i.is_equipped = 1", (user_id,))
    res = cursor.fetchone()
    update_character_stats(user_id, equip_str=res[0] or 0, equip_def=res[1] or 0)
    conn.close()

def use_healing_potion(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT i.id FROM inventory i JOIN items it ON i.item_id = it.id WHERE i.user_id = ? AND it.type = 'potion' LIMIT 1", (user_id,))
    potion = cursor.fetchone()
    if potion:
        cursor.execute("UPDATE characters SET health = MIN(max_health, health + 50) WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM inventory WHERE id = ?", (potion[0],))
        conn.commit()
        conn.close()
        return True, 50
    conn.close()
    return False, 0

def get_all_races():
    return {
        'human': {'name': 'Человек'}, 'elf': {'name': 'Эльф'},
        'dwarf': {'name': 'Дварф'}, 'orc': {'name': 'Орк'}
    }

def get_shop_items():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    res = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return res
