import vk_api

class User:
    def __init__(self, vk_session, db):
        self.vk_session = vk_session
        self.vk = vk_session.get_api()
        self.db = db

    def search_users(self, user_id):
        """Поиск пользователей, соответствующих заданному ID пользователя, возрасту, городу, полу и семейному положению."""
        try:
            user_info = self.vk.users.get(user_ids=user_id, fields='sex, bdate, city')[0]
            self.db.save_user(user_info)

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
                self.db.save_user(result)

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