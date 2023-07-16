import vk_api
import json
import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from config import group_token, user_token, V
from database import session, save_to_db, delete_from_db
from models import User, DatingUser, Photos, BlackList
from cache import cache_vk_api_decorator

# Для работы с ВК API
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)


# Ищет людей по заданным критериям
@cache_vk_api_decorator
def search_users(sex, age_from, age_to, city):
    vk_ = vk_api.VkApi(token=user_token)
    response = vk_.method('users.search', {
        'sort': 1,
        'sex': sex,
        'status': 1,
        'age_from': age_from,
        'age_to': age_to,
        'has_photo': 1,
        'count': 50,
        'online': 1,
        'hometown': city
    })
    all_persons = []
    link_profile = 'https://vk.com/id'
    for element in response['items']:
        person = [
            element['first_name'],
            element['last_name'],
            link_profile + str(element['id']),
            element['id']
        ]
        all_persons.append(person)
    return all_persons


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
    except vk_api.exceptions.ApiError:
        return ['нет доступа к фото']
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

    print(f'Информация о загруженных файлах успешно записана в json файл.')


# Регистрация пользователя
def register_user(vk_id):
    try:
        new_user = User(vk_id=vk_id)
        save_to_db(new_user)
        return True
    except (IntegrityError, InvalidRequestError):
        return False


# Добавление анкеты в избранное
def add_user_to_favorites(event_id, vk_id, first_name, last_name, city, link, user_id):
    user = User.get_user_by_vk_id(user_id)
    if not user:
        return False
    dating_user = DatingUser(
        vk_id=vk_id,
        first_name=first_name,
        last_name=last_name,
        city=city,
        link=link,
        user_id=user.id
    )
    try:
        save_to_db(dating_user)
        write_msg(event_id, 'ПОЛЬЗОВАТЕЛЬ УСПЕШНО ДОБАВЛЕН В ИЗБРАННОЕ')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id, 'Пользователь уже в избранном.')
        return False


# Добавление фото анкеты в избранное
def add_user_photo_to_favorites(event_id, link_photo, count_likes, dating_user_id):
    dating_user = DatingUser.get_by_id(dating_user_id)
    if not dating_user:
        return False
    photo = Photos(
        link_photo=link_photo,
        count_likes=count_likes,
        dating_user_id=dating_user.id
    )
    try:
        save_to_db(photo)
        write_msg(event_id, 'Фото пользователя сохранено в избранном')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id, 'Невозможно добавить фото этого пользователя (Уже сохранено)')
        return False


# Добавление пользователя в черный список
def add_user_to_blacklist(event_id, vk_id, first_name, last_name, city, link, link_photo, count_likes, user_id):
    user = User.get_user_by_vk_id(user_id)
    if not user:
        return False
    blacklisted_user = BlackList(
        vk_id=vk_id,
        first_name=first_name,
        last_name=last_name,
        city=city,
        link=link,
        link_photo=link_photo,
        count_likes=count_likes,
        user_id=user.id
    )
    try:
        save_to_db(blacklisted_user)
        write_msg(event_id, 'Пользователь успешно заблокирован.')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id, 'Пользователь уже в черном списке.')
        return False


# Удаление пользователя из избранного
def delete_user_from_favorites(ids):
    dating_user = DatingUser.get_by_vk_id(ids)
    if not dating_user:
        return False
    try:
        delete_from_db(dating_user)
        return True
    except (IntegrityError, InvalidRequestError):
        return False


# Удаление пользователя из черного списка
def delete_user_from_blacklist(ids):
    blacklisted_user = BlackList.get_by_vk_id(ids)
    if not blacklisted_user:
        return False
    try:
        delete_from_db(blacklisted_user)
        return True
    except (IntegrityError, InvalidRequestError):
        return False


# Запись сообщения пользователю
def write_msg(user_id, message):
    vk.method('messages.send',
              {'user_id': user_id,
               'message': message,
               'random_id': vk_api.utils.get_random_id()})


# Обработка событий ВК
def handle_vk_events():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == '/start':
                register_user(event.user_id)
                write_msg(event.user_id, 'Вы зарегистрированы.')
            elif event.text == '/search':
                search_users(event.user_id)
            elif event.text == '/add_to_favorites':
                add_user_to_favorites(event.user_id)
            elif event.text == '/add_photo_to_favorites':
                add_user_photo_to_favorites(event.user_id)
            elif event.text == '/add_to_blacklist':
                add_user_to_blacklist(event.user_id)
            elif event.text == '/delete_from_favorites':
                delete_user_from_favorites(event.user_id)
            elif event.text == '/delete_from_blacklist':
                delete_user_from_blacklist(event.user_id)


if __name__ == '__main__':
    handle_vk_events()