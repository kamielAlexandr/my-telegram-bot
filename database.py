def create_character(user_id, username, character_name, race):
    """Создание нового персонажа"""
    conn = None
    cursor = None
    try:
        if race not in RACES:
            return False, "Неизвестная раса"
        
        race_data = RACES[race]
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже персонаж у пользователя
        cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            return False, "У вас уже есть персонаж!"
        
        # Создаем персонажа с характеристиками расы
        cursor.execute("""
            INSERT INTO player_characters 
            (user_id, character_name, race, level, experience,
             strength, agility, intelligence, health, max_health, mana, max_mana, gold)
            VALUES (%s, %s, %s, 1, 0, %s, %s, %s, %s, %s, %s, %s, 100)
        """, (
            user_id, character_name, race,
            race_data['strength'], race_data['agility'], race_data['intelligence'],
            race_data['health'], race_data['health'],
            race_data['mana'], race_data['mana']
        ))
        
        conn.commit()
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
