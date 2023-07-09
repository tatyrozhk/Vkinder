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

            # Создание таблицы "matches", если она не существует
            self.db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    photos TEXT,
                    link TEXT
                )
                """
            )

            self.db_conn.commit()
            print("База данных успешно создана.")
        except sqlite3.Error as e:
            print("Ошибка при создании базы данных:", e)

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

    def close_connection(self):
        """Закрытие соединения с базой данных."""
        if self.db_conn:
            self.db_conn.close()
            print("Соединение с базой данных успешно закрыто.")