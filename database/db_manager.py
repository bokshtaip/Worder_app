import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="worder.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def init_db(self):
        if not os.path.exists(self.db_path):
            conn = self.connect()
            with open('database/db_schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()
            conn.close()
            print("База данных успешно создана.")
        else:
            print("База данных уже существует.")

    def execute_query(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.lastrowid

    def fetch_all(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()