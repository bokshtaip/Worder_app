import sqlite3
import os

db_file = None
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".db"):
            db_file = os.path.join(root, file)
            break
    if db_file:
        break

if db_file:
    print(f"Найден файл БД: {os.path.abspath(db_file)}")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(reviews)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Колонки в таблице reviews: {columns}")
    conn.close()
else:
    print("Файл .db не найден!")

input("\nНажмите Enter для выхода...")