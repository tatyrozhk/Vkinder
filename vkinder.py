import vk_api
import json
import datetime
from vk_api.longpoll import VkLongPoll
from config import group_token, user_token
from database import engine, Session
from cache import cache_vk_api_decorator

# Для работы с VK API
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

# Для работы с БД
session = Session()
connection = engine.connect()

count = 30

# Функция получения информации о пользователе по его vk_id
def get_user_info(vk_id):
    vk_ = vk_api.VkApi(token=user_token)
    try:
        response = vk_.method('users.get', {
            'user_ids': vk_id,
            'fields': 'first_name,last_name'
        })
        if response and 'response' in response:
            user_info = response['response'][0]  # Получаем первого пользователя из ответа
            return user_info
        else:
            print(f"Пользователь с vk_id={vk_id} не найден.")
            return None
    except vk_api.exceptions.ApiError as e:
        # Обработка ошибки API VK
        print(f"Ошибка API VK: {e}")
        return None
    except Exception as e:
        # Обработка других ошибок
        print(f"Ошибка: {e}")
        return None

# Ищет людей по заданным критериям с использованием сдвига offset
@cache_vk_api_decorator
def search_users(sex, age_from, age_to, city):
    vk_ = vk_api.VkApi(token=user_token)
    count = 30

    try:
        all_persons = []
        link_profile = 'https://vk.com/id'
        offset = 0
        while True:
            response = vk_.method('users.search', {
                'sort': 1,
                'sex': sex,
                'status': 1,
                'age_from': age_from,
                'age_to': age_to,
                'has_photo': 1,
                'count': count,
                'offset': offset,
                'online': 1,
                'hometown': city
            })
            items = response['items']
            if not items:
                break
            all_persons.extend(items)  # Изменили append на extend, чтобы добавлять информацию о пользователях, а не только их id
            offset += count
        return all_persons
    except vk_api.exceptions.ApiError as e:
        # Обработка ошибки API VK
        print(f"Ошибка API VK: {e}")
        return []
    except Exception as e:
        # Обработка других ошибок
        print(f"Ошибка: {e}")
        return []


# Получает фото профиля пользователя
@cache_vk_api_decorator
def get_profile_photos(anket_id):
    vk_ = vk_api.VkApi(token=user_token)
    try:
        response = vk_.method('photos.get', {
            'owner_id': anket_id,
            'album_id': 'profile',
            'count': 30,
            'extended': 1,
            'photo_sizes': 1,
        })
        users_photos = []
        for i in range(30):
            try:
                users_photos.append('photo' + str(response['items'][i]['owner_id']) + '_' + str(response['items'][i]['id']))
            except IndexError:
                users_photos.append('нет фото.')
        return users_photos
    except vk_api.exceptions.ApiError as e:
        # Обработка ошибки API VK
        print(f"Ошибка API VK: {e}")
        return []
    except Exception as e:
        # Обработка других ошибок
        print(f"Ошибка: {e}")
        return []


# Сортирует фото по количеству лайков и удаляет пустые элементы
def sort_photos_by_likes(photos):
    result = []
    for photo in photos:
        if photo != ['нет фото.'] and photo != 'нет доступа к фото':
            result.append(photo)
    sorted_photos = sorted(result)
    return sorted_photos


# Создает JSON-файл с результатами
def create_result_json(lst):
    today = datetime.date.today()
    today_str = f'{today.day}.{today.month}.{today.year}'
    res_list = []  # Создаем пустой список для хранения информации о пользователях
    for user_info in lst:
        res = {}  # Создаем новый словарь для каждого пользователя
        res['data'] = today_str
        res['first_name'] = user_info['first_name']
        res['second_name'] = user_info['last_name']
        res['link'] = f'https://vk.com/id{user_info["id"]}'
        res['id'] = user_info['id']
        res_list.append(res)

    with open("result.json", "w", encoding='UTF-8') as write_file:
        json.dump(res_list, write_file, ensure_ascii=False)
    print('Информация о загруженных файлах успешно записана в json файл.')
