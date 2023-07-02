import os
import json
import sqlite3
from getpass import getpass
import vk_api
from vk_api.exceptions import AuthError
from random import randrange


class VKinder:
    def __init__(self):
        self.vk_session = None
        self.vk = None
        self.db_conn = None
        self.db_cursor = None

    def authenticate(self):
        """Аутентификация в VK с использованием токена доступа."""
        access_token = getpass("Введите ваш токен доступа VK: ")
        try:
            self.vk_session = vk_api.VkApi(token=access_token)
            self.vk = self.vk_session.get_api()
            print("Аутентификация прошла успешно.")
        except AuthError as e:
            print("Аутентификация не удалась. Ошибка:", e)

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

    def search_users(self, user_id):
        """Поиск пользователей, соответствующих заданному ID пользователя, возрасту, городу, полу и семейному положению."""
        try:
            user_info = self.vk.users.get(user_ids=user_id, fields='sex, bdate, city')[0]
            self.save_user(user_info)

            # Получение предпочтений пользователя для поиска
            min_age = int(input("Введите минимальный возраст: "))
            max_age = int(input("Введите максимальный возраст: "))
            city = input("Введите город: ")
            sex = int(input("Введите пол (1 - женский, 2 - мужской): "))
            relationship_status = int(input("Введите семейное положение (0 - не указано): "))

            # Выполнение поиска на основе предпочтений пользователя
            search_params = {
                'count': 10,
                'sex': sex,
                'status': relationship_status,
                'age_from': min_age,
                'age_to': max_age,
                'city': city,
                'fields': 'sex, bdate, city',
            }
            search_results = self.vk.users.search(**search_params)

            for result in search_results['items']:
                self.save_user(result)

                # Получение топ-3 популярных фотографий пользователя
                photos_params = {
                    'owner_id': result['id'],
                    'album_id': 'profile',
                    'extended': 1,
                    'photo_sizes': 1,
                    'count': 100,
                }
                photos_response = self.vk.photos.get(**photos_params)
                photos = photos_response['items']

                # Сортировка фотографий по сумме лайков и комментариев
                photos.sort(key=lambda x: x['likes']['count'] + x['comments']['count'], reverse=True)

                # Выбор топ-3 фотографий
                top_photos = photos[:3]

                # Подготовка вложений фотографий и ссылки
                attachments = ','.join([f"photo{p['owner_id']}_{p['id']}" for p in top_photos])
                link = f"https://vk.com/id{result['id']}"

                # Отправка фотографий и ссылки пользователю
                self.vk.messages.send(user_id=user_id, attachment=attachments, message=link)

            print("Поиск успешно завершен.")

        except vk_api.VkApiError as e:
            print("Ошибка при поиске пользователей:", e)

    def run(self):
        self.authenticate()
        self.create_database()

        # Запрос ID пользователя для поиска
        user_id = input("Введите ваш ID пользователя VK: ")
        self.search_users(user_id)

        # Закрытие соединения с базой данных
        self.db_conn.close()