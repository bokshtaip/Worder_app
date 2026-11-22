CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    foreign_word TEXT NOT NULL,
    translation TEXT NOT NULL,
    transcription TEXT,
    collection_id INTEGER,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER,
    user_id INTEGER,
    quality INTEGER CHECK(quality BETWEEN 0 AND 5),
    next_review_date TIMESTAMP,
    interval_days INTEGER DEFAULT 1,
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO users (username, password_hash, role) VALUES
('admin', 'hash_admin_123', 'admin'),
('student', 'hash_student_123', 'user');

INSERT INTO collections (name, description, owner_id) VALUES
('Еда', 'Слова на тему еды', 1),
('Путешествия', 'Слова для поездок', 2);

INSERT INTO words (foreign_word, translation, transcription, collection_id) VALUES
('Apple', 'Яблоко', '[ˈæp.əl]', 1),
('Bread', 'Хлеб', '[bred]', 1),
('Cheese', 'Сыр', '[tʃiːz]', 1),
('Water', 'Вода', '[ˈwɔːtər]', 1),
('Meat', 'Мясо', '[miːt]', 1),
('Airport', 'Аэропорт', '[ˈeəpɔːt]', 2),
('Ticket', 'Билет', '[ˈtɪkɪt]', 2),
('Luggage', 'Багаж', '[ˈlʌɡɪdʒ]', 2),
('Passport', 'Паспорт', '[ˈpɑːspɔːt]', 2),
('Hotel', 'Отель', '[həʊˈtel]', 2);

INSERT INTO reviews (word_id, user_id, quality, next_review_date, interval_days) VALUES
(1, 2, 4, '2026-05-20 10:00:00', 3),
(2, 2, 5, '2026-05-25 10:00:00', 7),
(3, 2, 2, '2026-05-15 10:00:00', 1);