import sys
import bcrypt
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
import styles
from database.db_manager import DatabaseManager


class LoginWindow(QWidget):
    def __init__(self, main_app_class):
        super().__init__()
        self.main_app_class = main_app_class
        self.setWindowTitle("Worder — Вход")
        self.setFixedSize(400, 500)
        self.setStyleSheet(styles.MAIN_STYLE)

        self.db = DatabaseManager()
        self.db.connect()
        self.db.init_db()
        self._ensure_test_users()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("Вход в систему")
        title.setStyleSheet(
            f"font-family: {styles.FONT_HEADER}; font-size: 28px; font-weight: bold; color: {styles.COLOR_TEXT_MAIN};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        lbl_login = QLabel("Логин")
        lbl_login.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED}; font-size: 14px;")

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Введите логин")
        self.input_login.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 12px; font-size: 16px; }}
            QLineEdit:focus {{ border-color: {styles.COLOR_ACCENT}; }}
        """)

        lbl_password = QLabel("Пароль")
        lbl_password.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED}; font-size: 14px;")

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Введите пароль")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 12px; font-size: 16px; }}
            QLineEdit:focus {{ border-color: {styles.COLOR_ACCENT}; }}
        """)

        form_layout.addWidget(lbl_login)
        form_layout.addWidget(self.input_login)
        form_layout.addWidget(lbl_password)
        form_layout.addWidget(self.input_password)
        layout.addLayout(form_layout)

        btn_enter = QPushButton("Войти")
        btn_enter.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_enter.setFixedHeight(50)
        btn_enter.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_ACCENT}; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #4C6EF5; }}
            QPushButton:pressed {{ background-color: #2C4AB5; }}
        """)
        btn_enter.clicked.connect(self.handle_login)
        layout.addWidget(btn_enter)

        info_label = QLabel("Тестовые аккаунты:\nadmin / admin123\nuser / user123")
        info_label.setStyleSheet(
            f"color: {styles.COLOR_TEXT_MUTED}; font-size: 12px; text-align: center; margin-top: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def _ensure_test_users(self):
        test_users = [('admin', 'admin123', 'admin'), ('user', 'user123', 'user')]
        for username, password, role in test_users:
            try:
                check = self.db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                if check:
                    self.db.execute_query("UPDATE users SET password_hash = ?, role = ? WHERE username = ?",
                                          (hashed, role, username))
                else:
                    self.db.execute_query("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                          (username, hashed, role))
            except Exception as e:
                print(f"Ошибка инициализации пользователя {username}: {e}")

    def handle_login(self):
        login = self.input_login.text().strip()
        password = self.input_password.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        try:
            query = "SELECT id, username, password_hash, role FROM users WHERE username = ?"
            result = self.db.fetch_one(query, (login,))

            if result and bcrypt.checkpw(password.encode('utf-8'), result['password_hash'].encode('utf-8')):
                self.user_id = result['id']
                self.username = result['username']
                self.role = result['role']

                self.log_action("LOGIN_SUCCESS")

                app_instance = self.main_app_class(self.user_id, self.username, self.role)
                app_instance.show()
                self.hide()
            else:
                self.log_action("LOGIN_FAILED")
                QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))

    def log_action(self, action_type):
        try:
            query = "INSERT INTO action_log (user_id, action_type, entity_type, details) VALUES (?, ?, 'AUTH', ?)"
            uid = getattr(self, 'user_id', None)
            self.db.execute_query(query, (uid, action_type, f"Login attempt for '{self.input_login.text()}'"))
        except:
            pass