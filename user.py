import vk_api

class User:
    def __init__(self, vk_session, db):
        self.vk_session = vk_session
        self.vk = vk_session.get_api()
        self.db = db

    def search_users(self):
        """Поиск пользователей."""
        try:
            # Ваш код для поиска пользователей
            user_id = input("Введите ваш ID пользователя VK: ")

            min_age = int(input("Введите минимальный возраст: "))
            max_age = int(input("Введите максимальный возраст: "))
            city = input("Введите город: ")
            sex = int(input("Введите пол (1 - женский, 2 - мужской): "))
            relationship_status = int(input("Введите семейное положение (0 - не указано): "))

            search_params = {
                'count': 100,
                'sex': sex,
                'status': relationship_status,
                'age_from': min_age,
                'age_to': max_age,
                'city': city,
                'fields': 'sex, bdate, city',
            }

            search_results = self.vk.users.search(**search_params)

            for result in search_results['items']:
                user_data = {
                    'id': result['id'],
                    'first_name': result.get('first_name', ''),
                    'last_name': result.get('last_name', ''),
                    'sex': result.get('sex', 0),
                    'bdate': result.get('bdate', ''),
                    'city': result.get('city', {}).get('title', '')
                }

                self.db.save_user(user_data)

                # Получение топ-3 популярных фотографий пользователя
                photos_params = {
                    'owner_id': result['id'],
                    'album_id': 'profile',
                    'extended': 1,
                    'photo_sizes': 1,
                    'count': 3,
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