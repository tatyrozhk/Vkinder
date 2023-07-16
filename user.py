import pytest
from vkinder import search_users, get_profile_photos, sort_photos_by_likes, create_result_json
from database import session
from models import User, DatingUser, Photos, BlackList
from vk_api.exceptions import ApiError


class TestVkinder:

    def setup_class(self):
        print('Метод setup_class')

    def setup(self):
        print('Метод setup')

    def teardown(self):
        print('Метод teardown')

    """
    Тесты по работе приложения
    """

    # Проверка поиска анкет
    @pytest.mark.parametrize('sex, age_from, age_to, city, result', [
        ('1', '18', '21', 'Москва', True)])
    def test_search_users(self, sex, age_from, age_to, city, result):
        assert search_users(sex, age_from, age_to, city) == result

    # Тест поиска фотографий
    @pytest.mark.parametrize('user_id, result', [('336261034', True)])
    def test_get_profile_photos(self, user_id, result):
        assert get_profile_photos(user_id) == result

    # Тест сортировки по лайкам
    @pytest.mark.parametrize('photos, result',
                             [(['1', 'photo_1', '2', 'photo_2', '3', 'photo_3'],
                               ['1', '2', '3', 'photo_1', 'photo_2', 'photo_3']), ])
    def test_sort_photos_by_likes(self, photos, result):
        assert sort_photos_by_likes(photos) == result

    # Тест создания JSON-файла
    def test_create_result_json(self):
        lst = [['John', 'Doe', 'https://vk.com/id123', 123], ['Jane', 'Smith', 'https://vk.com/id456', 456]]
        create_result_json(lst)

        with open("result.json", "r") as file:
            data = file.read()
            assert data == '[{"data": "16.7.2023", "first_name": "John", "second_name": "Doe", "link": "https://vk.com/id123", "id": 123}, {"data": "16.7.2023", "first_name": "Jane", "second_name": "Smith", "link": "https://vk.com/id456", "id": 456}]'

    """
    Тесты по работе Базы данных
    """

    # Тест первичной регистрации пользователя
    @pytest.mark.parametrize('vk_id, result', [('1', False), ('1', False), ('336261034', False)])
    def test_register_user(self, vk_id, result):
        assert register_user(vk_id) == result

    # Тест добавления анкеты в избранное
    @pytest.mark.parametrize('event_id, vk_id, first_name, last_name, city, link, user_id, result',
                             [('7717001', '2', 'goga', 'boba', 'Turkey', 'www.vkman.ru', '1', False)])
    def test_add_user_to_favorites(self, event_id, vk_id, first_name, last_name, city, link, user_id, result):
        assert add_user_to_favorites(event_id, vk_id, first_name, last_name, city, link, user_id) == result

    # Тест добавления фото анкеты в избранное
    @pytest.mark.parametrize('event_id, link_photo, count_likes, dating_user_id, result',
                             [('123', 'link_link', '2', '33502052', False)])
    def test_add_user_photo_to_favorites(self, event_id, link_photo, count_likes, dating_user_id, result):
        assert add_user_photo_to_favorites(event_id, link_photo, count_likes, dating_user_id) == result

    # Тест добавления пользователя в черный список
    @pytest.mark.parametrize(
        'event_id, vk_id, first_name, last_name, city, link, link_photo, count_likes, user_id, result',
        [('123', '12', '12434', '1251231', 'sdfsdfs', 'sfsdfsdfds', 'fsdfsdfs', '12', '123', False)])
    def test_add_user_to_blacklist(self, event_id, vk_id, first_name, last_name, city, link, link_photo, count_likes,
                                    user_id, result):
        assert add_user_to_blacklist(event_id, vk_id, first_name, last_name, city, link, link_photo, count_likes,
                                 user_id) == result

    def teardown_class(self):
        print('Метод teardown_class')