import sqlite3
from datetime import datetime, timedelta


def get_active_users_today():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    # Текущая дата в формате 'YYYY-MM-DD'
    today = datetime.now().strftime('%Y-%m-%d')

    # Считаем пользователей, у которых last_check начинается с сегодняшней даты
    cursor.execute('SELECT COUNT(*) FROM users WHERE last_check LIKE ?', (f'{today}%',))
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_active_users_yesterday():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    # Дата вчерашнего дня в формате 'YYYY-MM-DD'
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Считаем пользователей, у которых last_check начинается со вчерашней даты
    cursor.execute('SELECT COUNT(*) FROM users WHERE last_check LIKE ?', (f'{yesterday}%',))
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_active_users_week():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    # Дата 7 дней назад
    week_ago = datetime.now() - timedelta(days=7)

    # Считаем пользователей, у которых last_check между датой 7 дней назад и сейчас
    cursor.execute('SELECT COUNT(*) FROM users WHERE last_check >= ?', (week_ago.strftime('%Y-%m-%d %H:%M:%S'),))
    count = cursor.fetchone()[0]

    conn.close()
    return count


# Инициализация базы данных и создание таблицы
def init_db():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    # Создание таблицы пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            checks_count INTEGER DEFAULT 0,
            first_start TEXT,
            last_check TEXT
        )
    ''')

    conn.commit()
    conn.close()


def calculate_all_user():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    # Считаем пользователей, у которых last_check между датой 7 дней назад и сейчас
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]

    conn.close()
    return count


def delete_user(user):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    sql_query = "DELETE FROM users WHERE username = ?"
    username_to_delete = (user,)
    # Выполнение запроса
    cursor.execute(sql_query, username_to_delete)

    # Сохранение изменений
    conn.commit()

    # Закрытие соединения
    conn.close()


# Получение списка всех пользователей
def get_all_users():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()  # Получаем всех пользователей

    conn.close()
    return [f"'id':{user[0]}, 'username':@{user[1]},'count':{user[2]}"
            for user in users]  # Возвращаем список user_id


def get_id_users():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()  # Получаем всех пользователей

    conn.close()
    return [f"{user[0]}" for user in users]  # Возвращаем список user_id
def get_user_without_zero():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT username,checks_count FROM users WHERE checks_count>0')
    users = cursor.fetchall()  # Получаем всех пользователей

    conn.close()
    return [f"'@{user[0]} count - {user[1]}"
            for user in users]


# Добавление нового пользователя в базу данных
def add_user(user_id, username):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    # Получаем текущее время
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_start, last_check)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, now, now))

    conn.commit()
    conn.close()


# Обновление информации о последней проверке и увеличении счётчика проверок
def update_user_checks(user_id):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        UPDATE users
        SET checks_count = checks_count + 1, last_check = ?
        WHERE user_id = ?
    ''', (now, user_id))

    conn.commit()
    conn.close()


# Получение информации о пользователе
def get_user_info(user_id):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_info = cursor.fetchone()

    conn.close()
    return user_info
