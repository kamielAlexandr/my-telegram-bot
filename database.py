# database.py
import sqlite3
import os
import datetime
import shutil
import glob

class Database:
    def __init__(self, db_path='data/game_bot.db'):
        self.db_path = db_path
        self.data_dir = os.path.dirname(db_path)
        
        # Создаем папку для данных, если ее нет
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 Создана папка для данных: {self.data_dir}")
        
        # Создаем резервную копию
        self.create_backup()
        
        # Инициализируем БД
        self.init_db()
    
    def create_backup(self):
        """Создание резервной копии базы данных"""
        try:
            if os.path.exists(self.db_path):
                # Создаем папку для бэкапов
                backup_dir = 'backups'
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Формируем имя файла
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{backup_dir}/game_bot_{timestamp}.db"
                
                # Копируем файл
                shutil.copy2(self.db_path, backup_name)
                print(f"✅ Резервная копия создана: {backup_name}")
                
                # Удаляем старые бэкапы
                self.cleanup_old_backups(backup_dir)
                
                return backup_name
            else:
                print("🆕 База данных не найдена, будет создана новая")
        except Exception as e:
            print(f"⚠️ Не удалось создать резервную копию: {e}")
        return None
    
    def cleanup_old_backups(self, backup_dir, keep_last=5):
        """Удаление старых резервных копий"""
        try:
            backup_files = glob.glob(f"{backup_dir}/game_bot_*.db")
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            if len(backup_files) > keep_last:
                for file in backup_files[keep_last:]:
                    os.remove(file)
                    print(f"🗑️ Удален старый бэкап: {file}")
        except Exception as e:
            print(f"⚠️ Не удалось очистить старые бэкапы: {e}")
    
    def get_connection(self):
        """Создаем соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Включаем поддержку внешних ключей
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    character_name TEXT,
                    race TEXT,
                    level INTEGER DEFAULT 1,
                    exp INTEGER DEFAULT 0,
                    exp_to_next_level INTEGER DEFAULT 100,
                    skill_points INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    attack INTEGER DEFAULT 10,
                    defense INTEGER DEFAULT 5,
                    daily_hunts INTEGER DEFAULT 0,
                    last_hunt_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица инвентаря
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_type TEXT,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            
            # Проверяем состояние БД
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_count = cursor.fetchone()[0]
            
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            print(f"✅ База данных инициализирована")
            print(f"   📊 Пользователей: {user_count}")
            print(f"   📏 Размер файла: {file_size} байт")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                conn.close()
    
    # Остальные методы остаются без изменений
    def get_user(self, user_id):
        """Получение данных пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_user(self, user_id):
        """Получение данных пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        """Создание нового пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, exp_to_next_level) 
                VALUES (?, ?, ?, ?, 100)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            print(f"👤 Создан новый пользователь: {user_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def update_user(self, user_id, **kwargs):
        """Обновление данных пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if not kwargs:
                return False
            
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)
            
            cursor.execute(f'''
                UPDATE users 
                SET {set_clause}, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', values)
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка при обновлении пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def complete_character_creation(self, user_id, character_name, race):
        """Завершение создания персонажа"""
        try:
            race_bonuses = {
                'human': {'attack': 2, 'defense': 2, 'health': 20},
                'elf': {'attack': 5, 'defense': 0, 'health': 10},
                'orc': {'attack': 8, 'defense': 3, 'health': 30},
                'dwarf': {'attack': 3, 'defense': 8, 'health': 25}
            }
            
            if race in race_bonuses:
                bonus = race_bonuses[race]
                return self.update_user(
                    user_id,
                    character_name=character_name,
                    race=race,
                    attack=10 + bonus['attack'],
                    defense=5 + bonus['defense'],
                    health=100 + bonus['health'],
                    max_health=100 + bonus['health'],
                    coins=100
                )
            return self.update_user(user_id, character_name=character_name, race=race)
        except Exception as e:
            print(f"❌ Ошибка при создании персонажа: {e}")
            return False
    
    def add_exp(self, user_id, exp_amount):
        """Добавление опыта и проверка уровня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            skill_points_gained = 0
            
            # Проверяем повышение уровня
            while new_exp >= user['exp_to_next_level']:
                new_exp -= user['exp_to_next_level']
                new_level += 1
                skill_points_gained += 1
                exp_to_next = int(100 * (1.5 ** (new_level - 1)))
                
                self.update_user(
                    user_id,
                    level=new_level,
                    exp=new_exp,
                    exp_to_next_level=exp_to_next,
                    skill_points=user['skill_points'] + skill_points_gained
                )
                user = self.get_user(user_id)
            
            if exp_amount > 0 and skill_points_gained == 0:
                return self.update_user(user_id, exp=new_exp)
            
            return skill_points_gained > 0
        except Exception as e:
            print(f"❌ Ошибка при добавлении опыта: {e}")
            return False
    
    def add_coins(self, user_id, coins_amount):
        """Добавление монет пользователю"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_coins = max(0, user['coins'] + coins_amount)
            return self.update_user(user_id, coins=new_coins)
        except Exception as e:
            print(f"❌ Ошибка при добавлении монет: {e}")
            return False
    
    def can_hunt_today(self, user_id):
        """Проверка, может ли пользователь охотиться сегодня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0, 5
            
            today = datetime.date.today().isoformat()
            last_hunt_date = user['last_hunt_date']
            
            if last_hunt_date != today:
                self.update_user(user_id, daily_hunts=0, last_hunt_date=today)
                return True, 0, 5
            
            return user['daily_hunts'] < 5, user['daily_hunts'], 5
        except Exception as e:
            print(f"❌ Ошибка при проверке охоты: {e}")
            return False, 0, 5
    
    def increment_daily_hunts(self, user_id):
        """Увеличиваем счетчик охот за день"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            today = datetime.date.today().isoformat()
            
            if user['last_hunt_date'] != today:
                return self.update_user(user_id, daily_hunts=1, last_hunt_date=today)
            
            return self.update_user(user_id, daily_hunts=user['daily_hunts'] + 1)
        except Exception as e:
            print(f"❌ Ошибка при увеличении счетчика охот: {e}")
            return False
    
    def use_skill_point(self, user_id, stat):
        """Использование очка навыка"""
        try:
            user = self.get_user(user_id)
            if not user or user['skill_points'] < 1:
                return False
            
            improvements = {
                'attack': {'attack': user['attack'] + 2},
                'defense': {'defense': user['defense'] + 2},
                'health': {'max_health': user['max_health'] + 15, 'health': min(user['health'] + 15, user['max_health'] + 15)}
            }
            
            if stat not in improvements:
                return False
            
            improvement = improvements[stat]
            improvement['skill_points'] = user['skill_points'] - 1
            
            return self.update_user(user_id, **improvement)
        except Exception as e:
            print(f"❌ Ошибка при использовании очка навыка: {e}")
            return False
    
    def add_to_inventory(self, user_id, item_type, item_name, quantity=1):
        """Добавление предмета в инвентарь"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity FROM inventory 
                WHERE user_id = ? AND item_type = ? AND item_name = ?
            ''', (user_id, item_type, item_name))
            
            existing = cursor.fetchone()
            
            if existing:
                new_quantity = existing['quantity'] + quantity
                cursor.execute('''
                    UPDATE inventory SET quantity = ? 
                    WHERE id = ?
                ''', (new_quantity, existing['id']))
            else:
                cursor.execute('''
                    INSERT INTO inventory (user_id, item_type, item_name, quantity)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, item_type, item_name, quantity))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении в инвентарь: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_inventory(self, user_id):
        """Получение инвентаря пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT item_type, item_name, quantity 
                FROM inventory 
                WHERE user_id = ? AND quantity > 0
                ORDER BY item_type, item_name
            ''', (user_id,))
            
            items = cursor.fetchall()
            return [dict(item) for item in items]
        except Exception as e:
            print(f"❌ Ошибка при получении инвентаря: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def use_item(self, user_id, item_type, item_name):
        """Использование предмета из инвентаря"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity FROM inventory 
                WHERE user_id = ? AND item_type = ? AND item_name = ?
            ''', (user_id, item_type, item_name))
            
            item = cursor.fetchone()
            if not item or item['quantity'] < 1:
                return False
            
            if item['quantity'] == 1:
                cursor.execute('DELETE FROM inventory WHERE id = ?', (item['id'],))
            else:
                cursor.execute('''
                    UPDATE inventory SET quantity = quantity - 1 
                    WHERE id = ?
                ''', (item['id'],))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при использовании предмета: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_race_description(self, race):
        """Получить описание расы"""
        descriptions = {
            'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
            'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
            'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
            'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
        }
        return descriptions.get(race, "Неизвестная раса")
    
    def calculate_health_regeneration(self, user_data):
        """Рассчитывает регенерацию здоровья на основе времени"""
        try:
            last_active = datetime.datetime.strptime(user_data['last_active'], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            time_diff = (now - last_active).total_seconds() / 3600
            
            # Регенерация: 2% от макс. здоровья в час, максимум до 50% от макс. здоровья
            max_regeneration_percent = 0.5
            regeneration_per_hour = 0.02
            
            regen_amount = min(
                user_data['max_health'] * regeneration_per_hour * time_diff,
                user_data['max_health'] * max_regeneration_percent
            )
            
            if regen_amount > 0:
                new_health = min(user_data['health'] + regen_amount, user_data['max_health'])
                return int(new_health), int(regen_amount)
            
            return user_data['health'], 0
        except:
            return user_data['health'], 0
    
    def apply_health_regeneration(self, user_id):
        """Применяет регенерацию здоровья"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0
            
            new_health, regen_amount = self.calculate_health_regeneration(user)
            
            if regen_amount > 0:
                self.update_user(user_id, health=new_health)
                return True, regen_amount
            
            return False, 0
        except Exception as e:
            print(f"❌ Ошибка при регенерации здоровья: {e}")
            return False, 0
    
    def get_top_players(self, limit=5):
        """Получение топа игроков по уровню и опыту"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT character_name, race, level, exp, coins, attack, defense
                FROM users 
                WHERE character_name IS NOT NULL 
                ORDER BY level DESC, exp DESC, coins DESC
                LIMIT ?
            ''', (limit,))
            
            top_players = cursor.fetchall()
            return [dict(player) for player in top_players]
        except Exception as e:
            print(f"❌ Ошибка при получении топа игроков: {e}")
            return []
        finally:
            if conn:
                conn.close()

# Создаем экземпляр базы данных
db = Database()

