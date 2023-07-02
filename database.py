import sqlite3
import json

class Database:
    def __init__(self):
        self.db_conn = None
        self.db_cursor = None

    def create_database(self):
        """Создание базы данных SQLite и необходимых таблиц, если они не существуют."""
        try:
            self.db_conn = sqlite3.connect("vkinder.db")
            self.db_cursor = self.db_conn.cursor()

            # Создание таблицы "users", если она не существует
            self.db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    sex INTEGER,
                    bdate TEXT,
                    city TEXT
                )
                """
            )

            # Создание таблицы "matches", если она не существует
            self.db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    photos TEXT,
                    link TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """
            )

            self.db_conn.commit()
            print("База данных успешно создана.")
        except sqlite3.Error as e:
            print("Ошибка при создании базы данных:", e)

    def save_user(self, user_data):
        """Сохранение данных пользователя в базу данных."""
        user_id = user_data.get('id')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        sex = user_data.get('sex', 0)
        bdate = user_data.get('bdate', '')
        city = user_data.get('city', {}).get('title')

        if user_id and first_name and last_name:
            try:
                self.db_cursor.execute(
                    """
                    INSERT INTO users (id, first_name, last_name, sex, bdate, city) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, first_name, last_name, sex, bdate, city)
                )
                self.db_conn.commit()
                print("Данные пользователя успешно сохранены.")
            except sqlite3.Error as e:
                print("Ошибка при сохранении данных пользователя:", e)
        else:
            print("Неполные данные пользователя. Невозможно сохранить.")

    def save_match(self, user_id, match_data):
        """Сохранение данных о совпадении в базу данных."""
        try:
            self.db_cursor.execute(
                """
                INSERT INTO matches (user_id, id, name, photos, link) VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, match_data['id'], match_data['name'], json.dumps(match_data['photos']), match_data['link'])
            )
            self.db_conn.commit()
            print("Данные о совпадении успешно сохранены.")
        except sqlite3.Error as e:
            print("Ошибка при сохранении данных о совпадении:", e)