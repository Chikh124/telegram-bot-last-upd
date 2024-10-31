import sqlite3
from datetime import datetime

# Підключення до бази даних
conn = sqlite3.connect('data/tournament.db')
cursor = conn.cursor()



def get_db_connection():
    return sqlite3.connect('data/tournament.db')


# Створення таблиць, якщо їх ще немає
def create_tables():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            team_id INTEGER,
            steam_profile TEXT,
            registration_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            captain_id INTEGER,
            invite_code TEXT,
            creation_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            team_id INTEGER,
            user_id INTEGER,
            joined_date TEXT,
            PRIMARY KEY (team_id, user_id)
        )
    ''')

    conn.commit()


# Додавання нового користувача до таблиці users
def add_user(user):
    # Додаємо перевірку на наявність username, first_name, last_name
    username = user.username if user.username else 'unknown'
    first_name = user.first_name if user.first_name else 'unknown'
    last_name = user.last_name if user.last_name else 'unknown'

    # Виводимо значення полів для перевірки
    print(f"Отримані дані користувача - ID: {user.id}, Username: {username}, First name: {first_name}, Last name: {last_name}")

    # Вставляємо ці дані у базу даних
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, registration_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.id, username, first_name, last_name, datetime.now()))

    # Підтверджуємо зміни
    conn.commit()





# Оновлення Steam профілю користувача
def update_steam_profile(user_id, steam_profile):
    cursor.execute('UPDATE users SET steam_profile = ? WHERE user_id = ?', (steam_profile, user_id))
    conn.commit()


# Перевірка, чи користувач вже в команді
def check_user_team(user_id):
    cursor.execute('SELECT team_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else None



# Створення нової команди
import random
import string


def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_team(captain_id, team_name):
    invite_code = generate_invite_code()

    # Додаємо нову команду
    cursor.execute('''
        INSERT INTO teams (team_name, captain_id, invite_code, creation_date)
        VALUES (?, ?, ?, ?)
    ''', (team_name, captain_id, invite_code, datetime.now()))
    team_id = cursor.lastrowid
    conn.commit()

    # Оновлюємо команду для користувача
    cursor.execute('UPDATE users SET team_id = ? WHERE user_id = ?', (team_id, captain_id))
    conn.commit()

    # Перевіряємо, чи оновилось значення team_id для капітана
    cursor.execute('SELECT team_id FROM users WHERE user_id = ?', (captain_id,))
    result = cursor.fetchone()

    if result:  # Перевіряємо, чи результат не None
        print(f"Користувач {captain_id} тепер в команді {result[0]}")
    else:
        print(f"Не вдалося отримати team_id для капітана {captain_id}")  # Діагностичне повідомлення

    return invite_code


# Приєднання користувача до команди
def join_team(user_id, invite_code):
    cursor.execute('SELECT team_id, captain_id FROM teams WHERE invite_code = ?', (invite_code,))
    result = cursor.fetchone()
    if result:
        team_id = result[0]
        captain_id = result[1]

        # Перевіряємо, чи користувач вже є в команді
        cursor.execute('SELECT * FROM team_members WHERE team_id = ? AND user_id = ?', (team_id, user_id))
        exists = cursor.fetchone()
        if exists:
            print(f"Користувач {user_id} вже в команді {team_id}.")  # Діагностичне повідомлення
            return False, captain_id  # Користувач вже в команді

        # Перевіряємо кількість гравців у команді
        cursor.execute('SELECT COUNT(*) FROM team_members WHERE team_id = ?', (team_id,))
        count = cursor.fetchone()[0]
        print(f"Кількість гравців у команді {team_id}: {count}")  # Діагностичне повідомлення

        if count < 2:  # Максимум два гравці в команді
            # Оновлюємо таблицю users (додаємо team_id користувачу)
            cursor.execute('UPDATE users SET team_id = ? WHERE user_id = ?', (team_id, user_id))
            conn.commit()

            # Додаємо користувача до команди в таблиці team_members
            cursor.execute('INSERT INTO team_members (team_id, user_id, joined_date) VALUES (?, ?, ?)',
                           (team_id, user_id, datetime.now()))
            conn.commit()

            print(f"Користувач {user_id} успішно приєднався до команди {team_id}.")
            return True, captain_id  # Повертаємо True і ID капітана команди
        else:
            print(f"Команда {team_id} вже заповнена.")  # Діагностичне повідомлення
            return False, captain_id  # Команда вже заповнена
    else:
        print("Невірний код запрошення.")  # Діагностичне повідомлення
        return None, None  # Недійсний код запрошення


# Функція закриття з'єднання з базою даних
def close_connection():
    conn.close()

def get_team_members(team_id):
    cursor.execute('SELECT username, first_name, last_name FROM users WHERE team_id = ?', (team_id,))
    members = cursor.fetchall()
    print(f"Члени команди {team_id}: {members}")  # Діагностичне повідомлення
    return members


def create_ticket_tables():
    # Таблиця для зберігання тікетів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT,
            admin_id INTEGER DEFAULT NULL
        )
    ''')

    # Таблиця для зберігання відповідей на тікети
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            user_id INTEGER,  -- Додаємо стовпець user_id
            admin_id INTEGER,
            response TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()




def create_ticket(user_id, description):
    cursor.execute('''
        INSERT INTO tickets (user_id, description, status, created_at)
        VALUES (?, ?, 'open', ?)
    ''', (user_id, description, datetime.now()))
    conn.commit()
    return cursor.lastrowid  # Повертаємо ID новоствореного тікета


def add_ticket_response(ticket_id, user_id, response):
    cursor.execute('''
        INSERT INTO ticket_responses (ticket_id, user_id, response, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (ticket_id, user_id, response, datetime.now()))
    conn.commit()

    # Оновлення статусу тікета
    cursor.execute('''
        UPDATE tickets SET status = 'in_progress' WHERE ticket_id = ?
    ''', (ticket_id,))
    conn.commit()




def get_open_tickets():
    cursor.execute('SELECT ticket_id, user_id, description FROM tickets WHERE status = "open"')
    return cursor.fetchall()


def get_admin_ids():
    # Отримуємо user_id всіх адміністраторів (is_admin = 1)
    cursor.execute('SELECT user_id FROM users WHERE is_admin = 1')
    admin_ids = cursor.fetchall()  # Отримуємо всі знайдені результати

    # Повертаємо список ID адміністраторів
    return [admin[0] for admin in admin_ids]


def set_admin(user_id):
    cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
    conn.commit()

def add_admin_column():
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        conn.commit()
        print("Стовпець 'is_admin' успішно додано в таблицю 'users'.")
    except sqlite3.OperationalError as e:
        print(f"Помилка: {e}")

def get_user_id_by_ticket(ticket_id):
    cursor.execute('SELECT user_id FROM tickets WHERE ticket_id = ?', (ticket_id,))
    result = cursor.fetchone()
    print(f"Отримано user_id для тікета {ticket_id}: {result}")  # Додаємо логування
    return result[0] if result else None


def check_connection():
    try:
        conn.execute("SELECT 1")
        print("З'єднання з базою даних активне.")
    except sqlite3.ProgrammingError:
        print("З'єднання з базою даних було втрачено.")

def add_user_id_column_to_ticket_responses():
    try:
        cursor.execute('ALTER TABLE ticket_responses ADD COLUMN user_id INTEGER')
        conn.commit()
        print("Стовпець 'user_id' успішно додано до таблиці 'ticket_responses'.")
    except sqlite3.OperationalError as e:
        print(f"Помилка при додаванні стовпця 'user_id': {e}")


def add_match_to_db(match_date, match_time):
    cursor.execute("INSERT INTO matches (match_date, match_time) VALUES (?, ?)", (match_date, match_time))
    conn.commit()


def get_matches():
    cursor.execute("SELECT match_date, match_time FROM matches ORDER BY match_date, match_time")
    return cursor.fetchall()

def get_schedule():
    cursor.execute('SELECT * FROM matches ORDER BY match_time')
    return cursor.fetchall()

def delete_match(match_id):
    cursor.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
    conn.commit()

def get_teams_with_members():
    cursor.execute("""
        SELECT teams.team_name, users.username, users.first_name, users.last_name, users.steam_profile
        FROM teams
        LEFT JOIN users ON teams.team_id = users.team_id
        WHERE users.team_id IS NOT NULL
        ORDER BY teams.team_name, users.username
    """)
    return cursor.fetchall()


def delete_team(team_id):
    cursor.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
    cursor.execute("DELETE FROM users WHERE team_id = ?", (team_id,))
    conn.commit()

def update_payment_status(user_id, status):
    cursor.execute("UPDATE users SET payment_status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()


def check_payment_status(user_id):
    cursor.execute("SELECT payment_status FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Повертаємо стан оплати
    return None  # Якщо користувач не знайдений або немає статусу


def set_user_language(user_id, language):
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        # Оновлюємо мову користувача
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
        print(f"Мова {language} успішно оновлена для користувача {user_id}")
    else:
        # Якщо користувача немає, створюємо новий запис
        cursor.execute("INSERT INTO users (user_id, language) VALUES (?, ?)", (user_id, language))
        print(f"Мова {language} успішно збережена для нового користувача {user_id}")

    conn.commit()


def get_user_language(user_id, db):
    cursor = db.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        language = result[0]
        print(f"Мова користувача з БД: {language}")  # Додаємо логування
        return language
    else:
        print(f"Мова не знайдена для користувача {user_id}, повертається 'uk'.")  # Додаємо логування
        return 'uk'








def get_user_id_by_ticket(ticket_id):
    cursor.execute('SELECT user_id FROM tickets WHERE ticket_id = ?', (ticket_id,))
    result = cursor.fetchone()
    print(f"Отримано результат запиту для тікета {ticket_id}: {result}")  # Логування результату SQL-запиту
    return result[0] if result else None

def get_team_name(team_id):
    cursor.execute("SELECT team_name FROM teams WHERE team_id = ?", (team_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Назва команди
    return None

def update_ticket_description(ticket_id, description):
    cursor.execute("UPDATE tickets SET description = ? WHERE ticket_id = ?", (description, ticket_id))
    conn.commit()


