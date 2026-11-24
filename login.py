import sys
import bcrypt
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QDialog)
from PyQt6.QtCore import Qt
import styles
from database.db_manager import DatabaseManager


class RegisterDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Регистрация")
        self.setFixedSize(400, 350)
        self.setStyleSheet(styles.MAIN_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Создать новый аккаунт")
        title.setStyleSheet(
            f"font-family: {styles.FONT_HEADER}; font-size: 20px; font-weight: bold; color: {styles.COLOR_TEXT_MAIN};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Придумайте логин")
        self.input_login.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 10px; }}
        """)

        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText("Придумайте пароль")
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 10px; }}
        """)

        self.input_pass_confirm = QLineEdit()
        self.input_pass_confirm.setPlaceholderText("Подтвердите пароль")
        self.input_pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass_confirm.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 10px; }}
        """)

        layout.addWidget(self.input_login)
        layout.addWidget(self.input_pass)
        layout.addWidget(self.input_pass_confirm)

        btn_register = QPushButton("Зарегистрироваться")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.setFixedHeight(45)
        btn_register.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_SUCCESS}; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #1E6B31; }}
        """)
        btn_register.clicked.connect(self.handle_register)
        layout.addWidget(btn_register)

    def handle_register(self):
        login = self.input_login.text().strip()
        password = self.input_pass.text().strip()
        confirm = self.input_pass_confirm.text().strip()

        if not login or not password or not confirm:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if len(login) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен быть не менее 3 символов!")
            return

        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return

        try:
            existing = self.db.fetch_one("SELECT id FROM users WHERE username = ?", (login,))
            if existing:
                QMessageBox.warning(self, "Ошибка", "Этот логин уже занят!")
                return

            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.db.execute_query("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
                                  (login, hashed))

            QMessageBox.information(self, "Успех", f"Аккаунт '{login}' успешно создан!\nТеперь вы можете войти.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))


class LoginWindow(QWidget):
    def __init__(self, main_app_class):
        super().__init__()
        self.main_app_class = main_app_class
        self.main_window_instance = None

        self.setWindowTitle("Worder — Вход")
        self.setFixedSize(400, 550)
        self.setStyleSheet(styles.MAIN_STYLE)

        app = QApplication.instance()
        if app:
            app.setQuitOnLastWindowClosed(False)

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

        btn_register = QPushButton("Нет аккаунта? Зарегистрироваться")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {styles.COLOR_ACCENT}; border: none; font-size: 14px; text-decoration: underline; }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_register.clicked.connect(self.open_register)
        layout.addWidget(btn_register)

        info_label = QLabel("Тестовые аккаунты:\nadmin / admin123\nuser / user123")
        info_label.setStyleSheet(
            f"color: {styles.COLOR_TEXT_MUTED}; font-size: 12px; text-align: center; margin-top: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def open_register(self):
        dialog = RegisterDialog(self.db, self)
        dialog.exec()

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

                self.main_window_instance = self.main_app_class(self.user_id, self.username, self.role)
                self.main_window_instance.show()
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