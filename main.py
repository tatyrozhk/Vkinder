import vk_api
import json
import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from config import group_token, user_token, V
from database import session, register_user, add_user, add_user_photos, add_to_black_list, delete_user_from_favorites, delete_user_from_blacklist
from vkinder import search_users, get_photo, sort_likes, write_msg, go_to_favorites, go_to_blacklist

# Для работы с VK API
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)


if __name__ == '__main__':
    while True:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    message_text = event.text
                    user_id = event.user_id

                    if message_text.lower() == "VKinder":
                        write_msg(user_id,
                                  f"Привет от VKinder!\n"
                                  f"\nЕсли ты новичок - зарегайся.\n"
                                  f"Для регистрации введи - Да.\n"
                                  f"Если ты бывал здесь - начинай поиск.\n"
                                  f"\nФормат поиска - пол возраст_от-возраст-до город\n"
                                  f"Перейти в избранное нажмите - 2\n"
                                  f"Перейти в черный список - 0\n")
                        break

                    if message_text.lower() == 'да':
                        register_user(user_id)
                        write_msg(user_id, 'Ты зареган.).')
                        write_msg(user_id,
                                  f"VKinder - для активации бота\n")
                        break

                    if len(message_text) > 1:
                        sex = 0
                        if message_text[0:7].lower() == 'девушка':
                            sex = 1
                        elif message_text[0:7].lower() == 'парень':
                            sex = 2
                        age_range = message_text[8:10].split('-')
                        city = message_text[11:]
                        result = search_users(sex, age_range[0], age_range[1], city)
                        for res in result:
                            write_msg(user_id, f'{res[0]}, {res[1]}, {res[2]}')
                            write_msg(user_id, '1 - добавить в избранное, 0 - далее \nq - Выход')
                            for event in longpoll.listen():
                                if event.type == VkEventType.MESSAGE_NEW:
                                    if event.to_me:
                                        message_text = event.text
                                        user_id = event.user_id
                                        if message_text == '1':
                                            add_user(user_id, res[3], res[0], res[1], city, res[2], user_id)
                                            photos = get_photo(res[3])
                                            sorted_photos = sort_likes(photos)
                                            for photo in sorted_photos:
                                                add_user_photos(user_id, photo[1], photo[0], user_id)
                                        elif message_text.lower() == 'q':
                                            write_msg(user_id, 'VKinder - для активации бота.')
                                        break
                            if message_text.lower() == 'q':
                                write_msg(user_id, 'VKinder - для активации бота.')
                                break
                    elif message_text == '2':
                        go_to_favorites(user_id)
                    elif message_text == '0':
                        go_to_blacklist(user_id)
                    elif message_text == 'q':
                        write_msg(user_id, 'VKinder - для активации бота.')
                    break