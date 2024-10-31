def add_admin_column():
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        conn.commit()
        print("Стовпець 'is_admin' успішно додано в таблицю 'users'.")
    except sqlite3.OperationalError as e:
        print(f"Помилка: {e}")
