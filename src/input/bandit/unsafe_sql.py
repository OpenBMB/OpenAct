import sqlite3


def unsafe_query(database_path, user_input):
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    cursor.execute(query)
    return cursor.fetchall()
