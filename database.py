import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Константы для рас
RACES = {
    "human": {
        "name": "Человек",
        "strength": 10,
        "agility": 10,
        "intelligence": 10,
        "health": 100,
        "mana": 50,
        "racial_ability": "Адаптивность: +1 ко всем характеристикам"
    },
    "elf": {
        "name": "Эльф",
        "strength": 8,
        "agility": 14,
        "intelligence": 12,
        "health": 80,
        "mana": 100,
        "racial_ability": "Магический дар: +50% к мане, точные выстрелы"
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 14,
        "agility": 8,
        "intelligence": 9,
        "health": 120,
        "mana": 30,
        "racial_ability": "Каменная кожа: +20% к здоровью, сопротивление к магии"
    },
    "orc": {
        "name": "Орк",
        "strength": 16,
        "agility": 9,
        "intelligence": 6,
        "health": 110,
        "mana": 20,
        "racial_ability": "Ярость: двойной урон при низком здоровье"
    }
}

def get_connection():
    """Создание подключения к PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        db_host = os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('PGPORT', '5432')
        db_name = os.getenv('PGDATABASE', 'railway')
        db_user = os.getenv('PGUSER', 'postgres')
        db_password = os.getenv('PGPASSWORD', '')
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        try:
            return psycopg2.connect(database_url)
        except Exception as e2:
            print(f"❌ Не удалось подключиться к БД: {e2}")
            return None

def init_db():
    """Инициализация таблиц в базе данных"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для инициализации")
            return
        
        cursor = conn.cursor()
        
        # Создаем таблицу с правильной структурой
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_characters (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                character_name VARCHAR(100) NOT NULL,
                race VARCHAR(50) DEFAULT 'human' NOT NULL,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                strength INTEGER DEFAULT 10,
                agility INTEGER DEFAULT 10,
                intelligence INTEGER DEFAULT 10,
                health INTEGER DEFAULT 100,
                max_health INTEGER DEFAULT 100,
                mana INTEGER DEFAULT 50,
                max_mana INTEGER DEFAULT 50,
                gold INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                battle_wins INTEGER DEFAULT 0,
                battle_losses INTEGER DEFAULT 0
            )
        """)
        
        # Проверяем и добавляем недостающие колонки
        columns_to_check = [
            'race', 'level', 'experience', 'strength', 'agility', 'intelligence',
            'health', 'max_health', 'mana', 'max_mana', 'gold',
            'created_at', 'last_active', 'battle_wins', 'battle_losses'
        ]
        
        for column in columns_to_check:
            try:
                cursor.execute(f"SELECT {column} FROM player_characters LIMIT 1")
            except Exception as e:
                if 'column' in str(e) and 'does not exist' in str(e):
                    print(f"🔄 Добавляю колонку '{column}' в таблицу...")
                    if column == 'race':
                        cursor.execute(f"ALTER TABLE player_characters ADD COLUMN {column} VARCHAR(50) DEFAULT 'human' NOT NULL")
                    elif column in ['created_at', 'last_active']:
                        cursor.execute(f"ALTER TABLE player_characters ADD COLUMN {column} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    elif column in ['level', 'experience', 'strength', 'agility', 'intelligence', 
                                    'health', 'max_health', 'mana', 'max_mana', 'gold', 
                                    'battle_wins', 'battle_losses']:
                        cursor.execute(f"ALTER TABLE player_characters ADD COLUMN {column} INTEGER DEFAULT 0")
                    else:
                        cursor.execute(f"ALTER TABLE player_characters ADD COLUMN {column} VARCHAR(100)")
        
        conn.commit()
        print("✅ База данных инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_character(user_id, username, character_name, race):
    """Создание нового персонажа"""
    conn = None
    cursor = None
    try:
        if race not in RACES:
            return False, "Неизвестная раса"
        
        race_data = RACES[race]
        
        conn = get_connection()
        if not conn:
            return False, "Не удалось подключиться к базе данных"
        
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже персонаж у пользователя
        cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            return False, "У вас уже есть персонаж!"
        
        # Создаем персонажа с характеристиками расы
        cursor.execute("""
            INSERT INTO player_characters 
            (user_id, character_name, race, 
             strength, agility, intelligence, 
             health, max_health, mana, max_mana, gold)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 100)
        """, (
            user_id, character_name, race,
            race_data['strength'], race_data['agility'], race_data['intelligence'],
            race_data['health'], race_data['health'],
            race_data['mana'], race_data['mana']
        ))
        
        conn.commit()
        print(f"✅ Персонаж создан для user_id: {user_id}")
        return True, "Персонаж успешно создан!"
        
    except Exception as e:
        print(f"❌ Ошибка при создании персонажа: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка при создании персонажа: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_character(user_id):
    """Получение информации о персонаже"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для получения персонажа")
            return None
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM player_characters 
            WHERE user_id = %s
        """, (user_id,))
        
        character = cursor.fetchone()
        
        if character:
            # Обновляем время последней активности
            cursor.execute("""
                UPDATE player_characters 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = %s
            """, (user_id,))
            conn.commit()
        
        return character
        
    except Exception as e:
        print(f"❌ Ошибка при получении персонажа: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_races():
    """Получение списка всех рас"""
    return RACES

# ... остальные функции остаются без изменений ...
