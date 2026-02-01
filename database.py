import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_connection():
    """Создание подключения к PostgreSQL"""
    # Railway автоматически создает переменную DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    # Для локальной разработки
    if not database_url:
        database_url = os.getenv('DATABASE_URL_LOCAL', 'postgresql://postgres:password@localhost:5432/bot_db')
    
    return psycopg2.connect(database_url, sslmode='require')

def init_db():
    """Инициализация таблиц в базе данных"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Создание таблицы, если она не существует
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_characters (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                name VARCHAR(100) NOT NULL,
                strength INTEGER DEFAULT 0,
                agility INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """)
        
        conn.commit()
        print("✅ Таблица создана или уже существует")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблицы: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def save_character(user_id, name, strength, agility):
    """Сохранение персонажа в базу данных"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Вставка или обновление записи
        cursor.execute("""
            INSERT INTO player_characters (user_id, name, strength, agility)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                strength = EXCLUDED.strength,
                agility = EXCLUDED.agility
        """, (user_id, name, strength, agility))
        
        conn.commit()
        print(f"✅ Персонаж сохранен для user_id: {user_id}")
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_character(user_id):
    """Получение персонажа по user_id"""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT name, strength, agility, created_at
            FROM player_characters
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при получении: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()
