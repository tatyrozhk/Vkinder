import vk_api
#import psycopg2
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import group_token
from sqlalchemy.exc import IntegrityError, InvalidRequestError
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
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)


# Анкеты добавленные в избранное
class DatingUser(Base):
    __tablename__ = 'dating_user'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String)
    second_name = sq.Column(sq.String)
    city = sq.Column(sq.String)
    link = sq.Column(sq.String)
    id_user = sq.Column(sq.Integer, sq.ForeignKey('user.id', ondelete='CASCADE'))

# Анкеты в черном списке
class BlackList(Base):
    __tablename__ = 'black_list'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String)
    second_name = sq.Column(sq.String)
    city = sq.Column(sq.String)
    link = sq.Column(sq.String)
    link_photo = sq.Column(sq.String)
    count_likes = sq.Column(sq.Integer)
    id_user = sq.Column(sq.Integer, sq.ForeignKey('user.id', ondelete='CASCADE'))
    
# Фото избранных анкет
class Photos(Base):
    __tablename__ = 'photos'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    link_photo = sq.Column(sq.String)
    count_likes = sq.Column(sq.Integer)
    id_dating_user = sq.Column(sq.Integer, sq.ForeignKey('dating_user.id', ondelete='CASCADE'))

# Удаляет пользователя из черного списка
def delete_user_from_blacklist(ids):
    current_user = session.query(BlackList).filter_by(vk_id=ids).first()
    session.delete(current_user)
    session.commit()


# Удаляет пользователя из избранного
def delete_user_from_favorites(ids):
    current_user = session.query(DatingUser).filter_by(vk_id=ids).first()
    session.delete(current_user)
    session.commit()


# Проверяет, зарегистрирован ли пользователь бота в БД
def check_db_master(ids):
    current_user_id = session.query(User).filter_by(vk_id=ids).first()
    return current_user_id


# Проверяет, есть ли пользователь в БД
def check_db_user(ids):
    dating_user = session.query(DatingUser).filter_by(vk_id=ids).first()
    blocked_user = session.query(BlackList).filter_by(vk_id=ids).first()
    return dating_user, blocked_user


# Проверяет, есть ли пользователь в черном списке
def check_db_black(ids):
    current_users_id = session.query(User).filter_by(vk_id=ids).first()
    # Находим все анкеты из избранного, которые добавил данный пользователь
    all_users = session.query(BlackList).filter_by(user_id=current_users_id.id).all()
    return all_users


# Проверяет, есть ли пользователь в избранном
def check_db_favorites(ids):
    current_users_id = session.query(User).filter_by(vk_id=ids).first()
    # Находим все анкеты из избранного, которые добавил данный пользователь
    all_users = session.query(DatingUser).filter_by(user_id=current_users_id.id).all()
    return all_users


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
        new_user = User(vk_id=vk_id)
        session.add(new_user)
        session.commit()
        return True
    except (IntegrityError, InvalidRequestError):
        return False


# Сохранение выбранного пользователя в БД
def add_user_to_favorites(event_id, vk_id, first_name, second_name, city, link, id_user):
    try:
        new_user = DatingUser(
            vk_id=vk_id,
            first_name=first_name,
            second_name=second_name,
            city=city,
            link=link,
            id_user=id_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Пользователь успешно добавлен в избранное')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Пользователь уже в избранном.')
        return False

# Сохранение в БД фото добавленного пользователя
def add_user_photos(event_id, link_photo, count_likes, id_dating_user):
    try:
        new_user = Photos(
            link_photo=link_photo,
            count_likes=count_likes,
            id_dating_user=id_dating_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Фото пользователя сохранено в избранном')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Невозможно добавить фото этого пользователя(Уже сохранено)')
        return False
    
# Добавление пользователя в черный список
def add_user_to_blacklist(event_id, vk_id, first_name, second_name, city, link, link_photo, count_likes, id_user):
    try:
        new_user = BlackList(
            vk_id=vk_id,
            first_name=first_name,
            second_name=second_name,
            city=city,
            link=link,
            link_photo=link_photo,
            count_likes=count_likes,
            id_user=id_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Пользователь успешно заблокирован.')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Пользователь уже в черном списке.')
        return False

if __name__ == '__main__':
    Base.metadata.create_all(engine)