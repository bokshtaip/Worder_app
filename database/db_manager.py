import sqlite3
import hashlib
import os
import datetime


class DatabaseManager:
    def __init__(self, db_name="worder.db"):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def execute_query(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid

    def fetch_all(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def init_db(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.execute_query("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)

        self.execute_query("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER,
                foreign_word TEXT NOT NULL,
                translation TEXT NOT NULL,
                transcription TEXT,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL
            )
        """)

        self.execute_query("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                quality INTEGER DEFAULT 1,
                next_review_date TIMESTAMP,
                interval_days INTEGER DEFAULT 1,
                FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        self.execute_query("""
            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        self.seed_data()

    def seed_data(self):
        admin_hash = self.hash_password("admin123")
        user_hash = self.hash_password("user123")

        self.execute_query("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           ("admin", admin_hash, "admin"))
        self.execute_query("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           ("user", user_hash, "user"))

        self.execute_query(
            "INSERT OR IGNORE INTO collections (id, name, description) VALUES (1, 'Еда', 'Базовые продукты')")
        self.execute_query(
            "INSERT OR IGNORE INTO collections (id, name, description) VALUES (2, 'Путешествия', 'Аэропорт и город')")

        test_words = [
            (1, 1, 'Apple', 'Яблоко', '[ˈæp.əl]'),
            (2, 1, 'Bread', 'Хлеб', '[bred]'),
            (3, 1, 'Cheese', 'Сыр', '[tʃiːz]'),
            (4, 1, 'Water', 'Вода', '[ˈwɔːtər]'),
            (5, 1, 'Meat', 'Мясо', '[miːt]'),
            (6, 1, 'Milk', 'Молоко', '[mɪlk]'),
            (7, 1, 'Egg', 'Яйцо', '[eɡ]'),
            (8, 1, 'Rice', 'Рис', '[raɪs]'),
            (9, 1, 'Fish', 'Рыба', '[fɪʃ]'),
            (10, 1, 'Fruit', 'Фрукт', '[fruːt]'),
            (11, 2, 'Airport', 'Аэропорт', '[ˈeəpɔːt]'),
            (12, 2, 'Ticket', 'Билет', '[ˈtɪkɪt]'),
            (13, 2, 'Luggage', 'Багаж', '[ˈlʌɡɪdʒ]'),
            (14, 2, 'Passport', 'Паспорт', '[ˈpɑːspɔːt]'),
            (15, 2, 'Hotel', 'Отель', '[həʊˈtel]'),
            (16, 2, 'Train', 'Поезд', '[treɪn]'),
            (17, 2, 'Car', 'Машина', '[kɑːr]'),
            (18, 2, 'Road', 'Дорога', '[rəʊd]'),
            (19, 2, 'City', 'Город', '[ˈsɪti]'),
            (20, 2, 'Country', 'Страна', '[ˈkʌntri]'),
            (21, 2, 'Map', 'Карта', '[mæp]'),
            (22, 2, 'Guide', 'Гид', '[ɡaɪd]'),
            (23, 2, 'Trip', 'Поездка', '[trɪp]'),
            (24, 2, 'Flight', 'Рейс', '[flaɪt]'),
            (25, 2, 'Station', 'Станция', '[ˈsteɪʃn]')
        ]

        for word in test_words:
            self.execute_query(
                "INSERT OR IGNORE INTO words (id, collection_id, foreign_word, translation, transcription) VALUES (?, ?, ?, ?, ?)",
                word
            )

    def log_action(self, user_id, action):
        self.execute_query("INSERT INTO action_log (user_id, action) VALUES (?, ?)", (user_id, action))