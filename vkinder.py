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

# Ищет людей по заданным критериям с использованием сдвига offset
@cache_vk_api_decorator
def search_users(user_id, sex=None, age_from=None, age_to=None, city=None, count=50):
    vk_ = vk_api.VkApi(token=user_token)
    
    # Запрашиваем параметры у пользователя, если они не были переданы
    if not sex:
        vk_.method('messages.send', {
            'user_id': user_id,
            'message': 'Укажите пол (1 - женский, 2 - мужской):',
            'random_id': vk_api.utils.get_random_id()
        })
        response = vk_.method('messages.get', {'count': 1})
        sex = response['items'][0]['text']

    if not age_from:
        vk_.method('messages.send', {
            'user_id': user_id,
            'message': 'Укажите минимальный возраст:',
            'random_id': vk_api.utils.get_random_id()
        })
        response = vk_.method('messages.get', {'count': 1})
        age_from = response['items'][0]['text']

    if not age_to:
        vk_.method('messages.send', {
            'user_id': user_id,
            'message': 'Укажите максимальный возраст:',
            'random_id': vk_api.utils.get_random_id()
        })
        response = vk_.method('messages.get', {'count': 1})
        age_to = response['items'][0]['text']

    if not city:
        vk_.method('messages.send', {
            'user_id': user_id,
            'message': 'Укажите город:',
            'random_id': vk_api.utils.get_random_id()
        })
        response = vk_.method('messages.get', {'count': 1})
        city = response['items'][0]['text']

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
            for element in items:
                person = [
                    element['first_name'],
                    element['last_name'],
                    link_profile + str(element['id']),
                    element['id']
                ]
                all_persons.append(person)
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
def get_profile_photos(user_id):
    vk_ = vk_api.VkApi(token=user_token)
    try:
        response = vk_.method('photos.get', {
            'owner_id': user_id,
            'album_id': 'profile',
            'count': 10,
            'extended': 1,
            'photo_sizes': 1,
        })
        users_photos = []
        for i in range(10):
            try:
                users_photos.append([
                    response['items'][i]['likes']['count'],
                    'photo' + str(response['items'][i]['owner_id']) + '_' + str(response['items'][i]['id'])
                ])
            except IndexError:
                users_photos.append(['нет фото.'])
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
    res = {}
    res_list = []
    for num, info in enumerate(lst):
        res['data'] = today_str
        res['first_name'] = info[0]
        res['second_name'] = info[1]
        res['link'] = info[2]
        res['id'] = info[3]
        res_list.append(res.copy())

    with open("result.json", "a", encoding='UTF-8') as write_file:
        json.dump(res_list, write_file, ensure_ascii=False)
    print('Информация о загруженных файлах успешно записана в json файл.')