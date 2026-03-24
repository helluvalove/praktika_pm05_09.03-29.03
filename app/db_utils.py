import psycopg2

DB_CONFIG = {
    'dbname': 'mk_polesie',
    'user': 'postgres',
    'password': 'qwerty321',
    'host': 'localhost',
    'port': 5432
}

def get_connection():
    """Возвращает соединение с БД"""
    return psycopg2.connect(**DB_CONFIG)

def get_user(login):
    """Получает пользователя по логину"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password, role, is_blocked, failed_attempts FROM users WHERE login = %s", (login,))
    user = cur.fetchone()
    conn.close()
    return user

def update_failed_attempts(user_id, conn):
    """Увеличивает счётчик неудачных попыток, возвращает новое значение"""
    cur = conn.cursor()
    cur.execute("UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id = %s RETURNING failed_attempts", (user_id,))
    new_count = cur.fetchone()[0]
    conn.commit()
    return new_count

def block_user(user_id, conn):
    """Блокирует пользователя"""
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_blocked = true WHERE id = %s", (user_id,))
    conn.commit()

def reset_failed_attempts(user_id, conn):
    """Сбрасывает счётчик неудачных попыток"""
    cur = conn.cursor()
    cur.execute("UPDATE users SET failed_attempts = 0 WHERE id = %s", (user_id,))
    conn.commit()

def get_all_users():
    """Возвращает список всех пользователей"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, login, role, is_blocked, failed_attempts FROM users ORDER BY id")
    users = cur.fetchall()
    conn.close()
    return users

def add_user(login, password, role):
    """Добавляет нового пользователя, возвращает True при успехе, иначе False (логин уже существует)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE login = %s", (login,))
    if cur.fetchone():
        conn.close()
        return False
    cur.execute("INSERT INTO users (login, password, role, is_blocked, failed_attempts) VALUES (%s, %s, %s, false, 0)",
                (login, password, role))
    conn.commit()
    conn.close()
    return True

def update_user(user_id, password, role):
    """Обновляет пароль и роль пользователя"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = %s, role = %s WHERE id = %s", (password, role, user_id))
    conn.commit()
    conn.close()

def unblock_user(user_id, conn):
    """Разблокирует пользователя и сбрасывает счётчик попыток"""
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_blocked = false, failed_attempts = 0 WHERE id = %s", (user_id,))
    conn.commit()