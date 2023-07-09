from auth import Authenticator
from database import Database
from user import User

class VKinder:
    def __init__(self):
        self.authenticator = Authenticator()
        self.database = Database()
        self.user = None

    def run(self):
        self.authenticator.authenticate()
        self.database.create_database()
        self.user = User(self.authenticator.vk_session, self.database)
        self.user.search_users()

        # Закрытие соединения с базой данных
        self.database.close_connection()