import vk_api
#import psycopg2
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import group_token
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy import Column, Integer, String, ARRAY

#from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


#connection = psycopg2.connect(user="###", password="###")
#connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#cursor = connection.cursor()
#sql_create_database = cursor.execute('vkinder_db_tmp')
#cursor.close()
#connection.close()

# Подключение к БД
Base = declarative_base()

engine = sq.create_engine('postgresql://postgres:777@localhost:5432/postgres', client_encoding='utf8')
Session = sessionmaker(bind=engine)

# Для работы с БД
session = Session()
connection = engine.connect()

# Для работы с ВК
vk = vk_api.VkApi(token=group_token)

# Пользователь бота ВК
class User(Base):
    __tablename__ = 'postgres'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vk_id = Column(Integer, unique=True)
    favorites = Column(ARRAY(Integer), default=[])
    blacklist = Column(ARRAY(Integer), default=[])
    profile_photos = Column(ARRAY(String), default=[])
    favorites_photos = Column(ARRAY(String), default=[])


# Удаляет пользователя из черного списка
def delete_user_from_blacklist(event_id, vk_id):
    try:
        # Проверяем, существует ли пользователь с указанным vk_id в черном списке
        blacklisted_user = session.query(User).filter_by(vk_id=vk_id).first()

        # Если пользователь существует в черном списке, удаляем его
        if blacklisted_user:
            session.delete(blacklisted_user)
            session.commit()
            write_msg(event_id, 'Пользователь успешно удален из черного списка.')
            return True
        else:
            write_msg(event_id, 'Пользователь с указанным vk_id не найден в черном списке.')
            return False
    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка: {e}")
        write_msg(event_id, 'Произошла ошибка при удалении пользователя из черного списка.')
        return False


# Удаляет пользователя из избранного
def delete_user_from_favorites(event_id, vk_id):
    try:
        # Проверяем, существует ли пользователь с указанным vk_id в избранном
        favorite_user = session.query(User).filter_by(vk_id=vk_id).first()

        # Если пользователь существует в избранном, удаляем его
        if favorite_user:
            session.delete(favorite_user)
            session.commit()
            write_msg(event_id, 'Пользователь успешно удален из избранного.')
            return True
        else:
            write_msg(event_id, 'Пользователь с указанным vk_id не найден в избранном.')
            return False
    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка: {e}")
        write_msg(event_id, 'Произошла ошибка при удалении пользователя из избранного.')
        return False


# Проверяет, есть ли пользователь в БД
def check_db_user(vk_id):
    user = session.query(User).filter_by(vk_id=vk_id).first()
    return user, None if user else None

# Проверяет, зарегистрирован ли пользователь бота в БД
def check_db_master(vk_id):
    current_user_id = session.query(User).filter_by(vk_id=vk_id).first()
    return current_user_id

# Проверяет, есть ли пользователь в черном списке
def check_db_black(user_id):
    try:
        current_user = session.query(User).filter(User.vk_id == user_id).first()
        if current_user is not None:
            black_list = session.query(User).filter(User.vk_id.in_(current_user.blacklist)).all()
            return black_list
        else:
            return []
    except Exception as e:
        print(f"Ошибка при проверке черного списка: {e}")
        return []

# Проверяет, есть ли пользователь в избранном
def check_db_favorites(user_id):
    try:
        current_user = session.query(User).filter(User.vk_id == user_id).first()
        if current_user is not None:
            favorites = session.query(User).filter(User.vk_id.in_(current_user.favorites)).all()
            return favorites
        else:
            return []
    except Exception as e:
        print(f"Ошибка при проверке списка избранных: {e}")
        return []

# Пишет сообщение пользователю
def write_msg(user_id, message, attachment=None):
    vk.method('messages.send',
              {'user_id': user_id,
               'message': message,
               'random_id': vk_api.utils.get_random_id(),
               'attachment': attachment})


# Регистрация пользователя
def register_user(vk_id):
    try:
        # Check if the user with the given vk_id already exists in the database
        existing_user = session.query(User).filter_by(vk_id=vk_id).first()

        if existing_user:
            # If the user already exists, you can choose to update the existing record or ignore the insertion
            # For example, you can update the 'favorites' and 'blacklist' fields if needed
            existing_user.favorites = []
            existing_user.blacklist = []
            session.commit()
            write_msg(vk_id, 'Вы уже зарегистрированы. Ваши настройки были сброшены.')
        else:
            # If the user does not exist, create a new record with the given vk_id
            new_user = User(vk_id=vk_id)
            session.add(new_user)
            session.commit()
            write_msg(vk_id, 'Вы успешно зарегистрированы в системе Vkinder.')

        return True
    except (IntegrityError, InvalidRequestError):
        session.rollback()
        return False
    except Exception as e:
        print(f"Ошибка: {e}")
        session.rollback()
        return False

# Сохранение в БД фото добавленного пользователя
def add_user_photos(event_id, vk_id, photos):
    # Проверяем, есть ли пользователь с таким vk_id в базе данных
    user = check_db_master(vk_id)
    if user is not None:
        try:
            # Если у пользователя уже есть фото в анкете, добавляем новые фото в список
            if user.profile_photos is not None:
                user.profile_photos.extend(photos)
            else:
                user.profile_photos = photos
                
            # Сохраняем изменения в базе данных
            session.commit()
            write_msg(event_id, 'Фото пользователя сохранено в анкете')
            return True
        except (IntegrityError, InvalidRequestError):
            write_msg(event_id, 'Невозможно добавить фото этого пользователя')
            return False
    else:
        write_msg(event_id, 'Пользователь с таким vk_id не найден в базе данных')
        return False

# Сохранение выбранного пользователя в БД
def add_user_to_favorites(event_id, vk_id):
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Проверяем, существует ли уже пользователь с таким vk_id
        existing_user = session.query(User).filter_by(vk_id=vk_id).first()

        if existing_user:
            # Если пользователь уже существует, проверяем, что данный vk_id еще не содержится в списке избранных
            if vk_id not in existing_user.favorites:
                existing_user.favorites.append(vk_id)
                session.commit()
                write_msg(event_id, 'Пользователь успешно добавлен в избранное')
            else:
                write_msg(event_id, 'Пользователь уже в избранном.')
        else:
            # Если пользователь не существует, создаем новую запись с указанным vk_id в списке избранных
            new_user = User(vk_id=vk_id, favorites=[vk_id])
            session.add(new_user)
            session.commit()
            write_msg(event_id, 'Пользователь успешно добавлен в избранное')

        return True
    except IntegrityError as e:
        # Обработка ошибки уникальности
        print(f"Ошибка уникальности: {e}")
        session.rollback()
        return False
    except Exception as e:
        # Обработка других ошибок
        print(f"Ошибка: {e}")
        session.rollback()
        return False
    finally:
        session.close()

# Добавление пользователя в черный список
def add_user_to_blacklist(event_id, vk_id):
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Проверяем, существует ли уже пользователь с таким vk_id
        existing_user = session.query(User).filter_by(vk_id=vk_id).first()

        if existing_user:
            # Если пользователь уже существует, проверяем, что данный vk_id еще не содержится в списке черного списка
            if vk_id not in existing_user.blacklist:
                existing_user.blacklist.append(vk_id)
                session.commit()
                write_msg(event_id, 'Пользователь успешно добавлен в черный список')
            else:
                write_msg(event_id, 'Пользователь уже в черном списке.')
        else:
            # Если пользователь не существует, создаем новую запись с указанным vk_id в списке черного списка
            new_user = User(vk_id=vk_id, blacklist=[vk_id])
            session.add(new_user)
            session.commit()
            write_msg(event_id, 'Пользователь успешно добавлен в черный список')

        return True
    except IntegrityError as e:
        # Обработка ошибки уникальности
        print(f"Ошибка уникальности: {e}")
        session.rollback()
        return False
    except Exception as e:
        # Обработка других ошибок
        print(f"Ошибка: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == '__main__':
    Base.metadata.create_all(engine)