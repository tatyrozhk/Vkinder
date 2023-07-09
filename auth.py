from getpass import getpass
import vk_api
from vk_api.exceptions import AuthError

class Authenticator:
    def __init__(self):
        self.vk_session = None
        self.vk = None

    def authenticate(self):
        access_token = getpass("Введите ваш токен доступа VK: ")
        try:
            self.vk_session = vk_api.VkApi(token=access_token)
            self.vk = self.vk_session.get_api()
            print("Аутентификация прошла успешно.")
        except AuthError as e:
            print("Аутентификация не удалась. Ошибка:", e)