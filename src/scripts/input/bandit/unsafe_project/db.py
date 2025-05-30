# db.py
import sqlite3


def get_user_password(username):
    # 故意写的不安全的 SQL 查询
    query = "SELECT password FROM users WHERE username = '{}'".format(username)
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result
