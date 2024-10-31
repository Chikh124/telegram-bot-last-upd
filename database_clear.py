import sqlite3

# Підключення до бази даних
conn = sqlite3.connect('data/tournament.db')
cursor = conn.cursor()

# Очищення всіх таблиць
cursor.execute('DELETE FROM users')
cursor.execute('DELETE FROM teams')
cursor.execute('DELETE FROM team_members')

conn.commit()
conn.close()

print("База даних успішно очищена.")
