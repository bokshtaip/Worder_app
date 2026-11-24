import sys
import re
import csv
import shutil
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame, QLineEdit,
                             QStackedWidget, QStackedLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
                             QDialog, QDialogButtonBox, QTabWidget, QFormLayout)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QCloseEvent
import styles
from database.db_manager import DatabaseManager
import datetime
from login import LoginWindow


class AnimatedBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {styles.COLOR_BG};")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(styles.COLOR_BG))


class WorderApp(QMainWindow):
    def __init__(self, user_id, username, role):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.role = role

        self.setWindowTitle(f"Worder — {username} ({role})")
        self.setMinimumSize(1024, 768)
        self.setStyleSheet(styles.MAIN_STYLE)

        self.db = DatabaseManager()
        self.db.connect()
        self.db.init_db()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Создаем экраны
        self.dashboard_screen = self.create_dashboard()
        self.training_screen = self.create_training_screen()
        self.my_dict_screen = self.create_dict_screen(is_personal=True)
        self.all_words_screen = self.create_dict_screen(is_personal=False)
        self.about_screen = self.create_about_screen()

        # Фиксируем индексы базовых экранов
        self.stacked_widget.addWidget(self.dashboard_screen)  # 0
        self.stacked_widget.addWidget(self.training_screen)  # 1
        self.stacked_widget.addWidget(self.my_dict_screen)  # 2
        self.stacked_widget.addWidget(self.all_words_screen)  # 3
        self.stacked_widget.addWidget(self.about_screen)  # 4

        self.about_index = 4
        self.admin_index = -1

        # Админка всегда добавляется последней
        if self.role == 'admin':
            self.admin_screen = self.create_admin_screen()
            self.stacked_widget.addWidget(self.admin_screen)  # 5
            self.admin_index = 5

        self.stacked_widget.setCurrentIndex(0)

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.logout()

    def get_personal_words(self):
        try:
            query = """
                SELECT w.id, w.foreign_word, w.translation, w.transcription, r.quality
                FROM words w
                JOIN reviews r ON w.id = r.word_id AND r.user_id = ?
            """
            rows = self.db.fetch_all(query, (self.user_id,))
            words = []
            for row in rows:
                quality = row["quality"]
                if quality == 4:
                    status = "Выучено"
                elif quality == 5:
                    status = "Уже известно"
                else:
                    status = "На повторении"

                words.append({
                    "id": row["id"], "word": row["foreign_word"],
                    "trans": row["transcription"] or "", "ru": row["translation"], "status": status
                })
            return words
        except Exception as e:
            print(f"Ошибка загрузки личных слов: {e}")
            return []

    def get_all_words(self):
        try:
            query = "SELECT id, foreign_word, translation, transcription FROM words"
            rows = self.db.fetch_all(query)
            words = []
            for row in rows:
                words.append({
                    "id": row["id"], "word": row["foreign_word"],
                    "trans": row["transcription"] or "", "ru": row["translation"], "status": "В справочнике"
                })
            return words
        except Exception as e:
            print(f"Ошибка загрузки справочника: {e}")
            return []

    def get_stats_data(self):
        try:
            review_count = \
            self.db.fetch_one("SELECT COUNT(*) as count FROM reviews WHERE user_id = ?", (self.user_id,))['count']

            repeating = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM reviews WHERE user_id = ? AND quality NOT IN (4, 5)",
                (self.user_id,)
            )['count']

            learned = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM reviews WHERE user_id = ? AND quality = 4",
                (self.user_id,)
            )['count']

            known = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM reviews WHERE user_id = ? AND quality = 5",
                (self.user_id,)
            )['count']

            return {
                "total": review_count,
                "repeating": repeating,
                "learned": learned,
                "known": known
            }
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {"total": 0, "repeating": 0, "learned": 0, "known": 0}

    def update_dashboard_stats(self):
        stats = self.get_stats_data()
        stats_html = f"""
        <div style='font-family: {styles.FONT_HEADER}; color: {styles.COLOR_TEXT_MAIN};'>
            <div style='font-size: 24px; font-weight: bold; margin-bottom: 10px;'>Всего изучено: {stats["total"]}</div>
            <div style='font-size: 14px; color: {styles.COLOR_ACCENT};'>🔄 На повторении: {stats["repeating"]}</div>
            <div style='font-size: 14px; color: {styles.COLOR_SUCCESS};'>✅ Выучено: {stats["learned"]}</div>
            <div style='font-size: 14px; color: {styles.COLOR_TEXT_MUTED};'>💡 Уже известно: {stats["known"]}</div>
        </div>
        """
        self.lbl_stats_words.setText(stats_html)

    def create_dashboard(self):
        screen = QWidget()
        stacked_layout = QStackedLayout(screen)
        stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self.bg = AnimatedBackground()
        self.bg.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self.create_header())

        main_area = QHBoxLayout()
        main_area.setContentsMargins(40, 40, 40, 40)
        main_area.setSpacing(40)

        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        btn_review = self.create_menu_button("↻ К повторению сегодня")
        btn_learn = self.create_menu_button("+ Учить новые слова")
        btn_learn.clicked.connect(self.start_training)

        btn_my_dict = self.create_menu_button("📖 Мой словарь")
        btn_my_dict.clicked.connect(lambda: self.switch_screen(2))

        btn_all_words = self.create_menu_button("📚 Все слова приложения")
        btn_all_words.clicked.connect(lambda: self.switch_screen(3))

        if self.role == 'admin':
            btn_admin = self.create_menu_button("⚙️ Администрирование")
            btn_admin.clicked.connect(lambda: self.switch_screen(self.admin_index))
            left_column.addWidget(btn_admin)

        left_column.addWidget(btn_review)
        left_column.addWidget(btn_learn)
        left_column.addWidget(btn_my_dict)
        left_column.addWidget(btn_all_words)
        left_column.addStretch()

        right_column = QVBoxLayout()
        right_column.setSpacing(20)

        stats_panel = QFrame()
        stats_panel.setStyleSheet(
            f"background-color: {styles.COLOR_SURFACE}; border-radius: 12px; border: 1px solid {styles.COLOR_BORDER};")
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(20, 20, 20, 20)

        lbl_stats_title = QLabel("Статистика за неделю")
        lbl_stats_title.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED}; font-size: 14px;")

        stats = self.get_stats_data()
        stats_html = f"""
        <div style='font-family: {styles.FONT_HEADER}; color: {styles.COLOR_TEXT_MAIN};'>
            <div style='font-size: 24px; font-weight: bold; margin-bottom: 10px;'>Всего изучено: {stats["total"]}</div>
            <div style='font-size: 14px; color: {styles.COLOR_ACCENT};'>🔄 На повторении: {stats["repeating"]}</div>
            <div style='font-size: 14px; color: {styles.COLOR_SUCCESS};'>✅ Выучено: {stats["learned"]}</div>
            <div style='font-size: 14px; color: {styles.COLOR_TEXT_MUTED};'>💡 Уже известно: {stats["known"]}</div>
        </div>
        """
        self.lbl_stats_words = QLabel(stats_html)
        self.lbl_stats_words.setTextFormat(Qt.TextFormat.RichText)

        stats_layout.addWidget(lbl_stats_title)
        stats_layout.addWidget(self.lbl_stats_words)
        stats_layout.addStretch()

        right_column.addWidget(stats_panel)
        right_column.addStretch()

        main_area.addLayout(left_column, 1)
        main_area.addLayout(right_column, 2)
        content_layout.addLayout(main_area, 1)

        content_layout.addWidget(self.create_footer())

        stacked_layout.addWidget(self.bg)
        stacked_layout.addWidget(content_widget)
        stacked_layout.setCurrentIndex(1)

        return screen

    def create_training_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.create_header())

        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setContentsMargins(40, 20, 40, 20)

        btn_back = QPushButton("← На главную")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {styles.COLOR_TEXT_MUTED}; border: none; font-size: 14px; text-align: left; }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_back.clicked.connect(lambda: self.switch_screen(0))

        breadcrumbs = QLabel("Главная > Тренировка")
        breadcrumbs.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED};")

        breadcrumb_layout.addWidget(btn_back)
        breadcrumb_layout.addStretch()
        breadcrumb_layout.addWidget(breadcrumbs)
        layout.addLayout(breadcrumb_layout)

        self.center_area = QVBoxLayout()
        self.center_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(500, 300)
        self.card.setStyleSheet(f"""
            QFrame {{ background-color: {styles.COLOR_SURFACE}; border-radius: 16px; border: 1px solid {styles.COLOR_BORDER}; }}
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_word = QLabel("")
        self.lbl_word.setStyleSheet(
            f"font-family: {styles.FONT_HEADER}; font-size: 48px; font-weight: bold; color: {styles.COLOR_TEXT_MAIN};")
        self.lbl_word.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_transcription = QLabel("")
        self.lbl_transcription.setStyleSheet(f"font-size: 18px; color: {styles.COLOR_TEXT_MUTED};")
        self.lbl_transcription.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_ru = QLabel("")
        self.lbl_ru.setStyleSheet(f"font-size: 20px; color: {styles.COLOR_SUCCESS}; font-weight: bold;")
        self.lbl_ru.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ru.hide()

        btn_show = QPushButton("Показать перевод")
        btn_show.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_show.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_ACCENT}; color: white; border-radius: 8px; padding: 10px 20px; font-size: 16px; margin-top: 20px; }}
            QPushButton:hover {{ background-color: #4C6EF5; }}
        """)
        btn_show.clicked.connect(lambda: self.lbl_ru.show())

        card_layout.addWidget(self.lbl_word)
        card_layout.addWidget(self.lbl_transcription)
        card_layout.addWidget(self.lbl_ru)
        card_layout.addWidget(btn_show)

        self.center_area.addWidget(self.card)

        self.rating_layout = QHBoxLayout()
        self.rating_layout.setSpacing(20)
        self.rating_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_known = self.create_rating_button("Уже знаю", styles.COLOR_TEXT_MUTED)
        btn_again = self.create_rating_button("Показать ещё", styles.COLOR_ACCENT)
        btn_remembered = self.create_rating_button("Запомнил", styles.COLOR_SUCCESS)

        btn_known.clicked.connect(lambda: self.handle_answer(5))
        btn_again.clicked.connect(lambda: self.handle_answer(1))
        btn_remembered.clicked.connect(lambda: self.handle_answer(4))

        self.rating_layout.addWidget(btn_known)
        self.rating_layout.addWidget(btn_again)
        self.rating_layout.addWidget(btn_remembered)

        self.center_area.addLayout(self.rating_layout)
        layout.addLayout(self.center_area, 1)
        layout.addWidget(self.create_footer())

        return screen

    def create_dict_screen(self, is_personal=True):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.create_header())

        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setContentsMargins(40, 20, 40, 20)

        btn_back = QPushButton("← На главную")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {styles.COLOR_TEXT_MUTED}; border: none; font-size: 14px; text-align: left; }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_back.clicked.connect(lambda: self.switch_screen(0))

        title_text = "Главная > Мой словарь" if is_personal else "Главная > Все слова приложения"
        breadcrumbs = QLabel(title_text)
        breadcrumbs.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED};")

        breadcrumb_layout.addWidget(btn_back)
        breadcrumb_layout.addStretch()
        breadcrumb_layout.addWidget(breadcrumbs)
        layout.addLayout(breadcrumb_layout)

        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(40, 0, 40, 20)

        lbl_filter = QLabel("Фильтр:")
        lbl_filter.setStyleSheet(f"color: {styles.COLOR_TEXT_MAIN}; font-size: 14px;")

        combo_filter = QComboBox()
        if is_personal:
            combo_filter.addItems(["Все мои слова", "На повторении", "Выучено", "Уже известно"])
        else:
            combo_filter.addItems(["Все слова"])

        combo_filter.setStyleSheet(f"""
            QComboBox {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 4px; padding: 5px; min-width: 150px; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; selection-background-color: {styles.COLOR_ACCENT}; }}
        """)

        filter_layout.addWidget(lbl_filter)
        filter_layout.addWidget(combo_filter)

        # Поле поиска для экрана "Все слова"
        if not is_personal:
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("🔍 Поиск по словам...")
            self.search_input.setStyleSheet(f"""
                QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 4px; padding: 5px 10px; min-width: 200px; }}
            """)
            self.search_input.textChanged.connect(
                lambda text: self.filter_table(self.all_table, self.all_combo, False, text))
            filter_layout.addWidget(self.search_input)

        if is_personal:
            btn_reset = QPushButton("Сбросить прогресс")
            btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reset.setStyleSheet(f"""
                QPushButton {{ background-color: {styles.COLOR_ACCENT}; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold; }}
                QPushButton:hover {{ background-color: #2C4AB5; }}
            """)
            btn_reset.clicked.connect(self.reset_progress)
            filter_layout.addWidget(btn_reset)
        else:
            if self.role == 'admin':
                btn_add = QPushButton("➕ Добавить слово")
                btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_add.setStyleSheet(f"""
                    QPushButton {{ background-color: {styles.COLOR_SUCCESS}; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold; }}
                    QPushButton:hover {{ background-color: #1E6B31; }}
                """)
                btn_add.clicked.connect(self.open_add_word_dialog)
                filter_layout.addWidget(btn_add)

                btn_delete = QPushButton("🗑️ Удалить выбранное")
                btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_delete.setStyleSheet(f"""
                    QPushButton {{ background-color: #D93025; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold; }}
                    QPushButton:hover {{ background-color: #B02A1F; }}
                """)
                btn_delete.clicked.connect(self.delete_selected_word)
                filter_layout.addWidget(btn_delete)
            else:
                btn_load_test = QPushButton("Загрузить тестовые слова")
                btn_load_test.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_load_test.setStyleSheet(f"""
                    QPushButton {{ background-color: {styles.COLOR_SUCCESS}; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold; }}
                    QPushButton:hover {{ background-color: #1E6B31; }}
                """)
                btn_load_test.clicked.connect(self.load_test_words)
                filter_layout.addWidget(btn_load_test)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Слово", "Перевод", "Транскрипция", "Статус"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; gridline-color: {styles.COLOR_BORDER}; margin: 0 40px 20px 40px; }}
            QHeaderView::section {{ background-color: {styles.COLOR_BG}; color: {styles.COLOR_TEXT_MAIN}; border: none; padding: 5px; font-weight: bold; }}
            QTableWidget::item {{ padding: 10px; }}
        """)

        layout.addWidget(table)
        layout.addWidget(self.create_footer())

        if is_personal:
            self.my_table = table
            self.my_combo = combo_filter
            combo_filter.currentIndexChanged.connect(lambda: self.filter_table(self.my_table, self.my_combo, True))
        else:
            self.all_table = table
            self.all_combo = combo_filter

        return screen

    def delete_selected_word(self):
        selected_rows = self.all_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите слово для удаления!")
            return

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            "Вы уверены, что хотите удалить выбранное слово из общего справочника?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Берем ID из UserRole, а не из текста ячейки
                item = self.all_table.item(selected_rows[0].row(), 0)
                word_id = item.data(Qt.ItemDataRole.UserRole)

                if word_id is None:
                    raise ValueError("Не удалось определить ID слова")

                self.db.execute_query("DELETE FROM reviews WHERE word_id = ?", (word_id,))
                self.db.execute_query("DELETE FROM words WHERE id = ?", (word_id,))

                self.filter_table(self.all_table, self.all_combo, False)
                QMessageBox.information(self, "Успех", "Слово успешно удалено!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))

    def open_add_word_dialog(self):
        dialog = AddWordDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["word"] or not data["ru"]:
                QMessageBox.warning(self, "Ошибка", "Слово и перевод обязательны!")
                return

            if not re.search(r'[a-zA-Zа-яА-Я]', data["word"]):
                QMessageBox.warning(self, "Ошибка", "Слово должно содержать буквы!")
                return

            try:
                query = "INSERT INTO words (foreign_word, translation, transcription, collection_id) VALUES (?, ?, ?, 1)"
                self.db.execute_query(query, (data["word"], data["ru"], data["trans"]))
                self.filter_table(self.all_table, self.all_combo, False)
                QMessageBox.information(self, "Успех", f"Слово '{data['word']}' добавлено!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))

    def create_admin_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.create_header())

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; margin: 0 40px 20px 40px; }}
            QTabBar::tab {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; padding: 10px 20px; border: 1px solid {styles.COLOR_BORDER}; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
            QTabBar::tab:selected {{ background-color: {styles.COLOR_ACCENT}; color: white; }}
        """)

        users_tab = self._create_admin_users_tab()
        add_word_tab = self._create_admin_add_word_tab()
        stats_tab = self._create_admin_stats_tab()

        tabs.addTab(users_tab, "Пользователи")
        tabs.addTab(add_word_tab, "Добавить слово")
        tabs.addTab(stats_tab, "Статистика и Отчёты")

        layout.addWidget(tabs, 1)
        layout.addWidget(self.create_footer())

        return screen

    def _create_admin_users_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Логин", "Роль", "ID"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; gridline-color: {styles.COLOR_BORDER}; }}
            QHeaderView::section {{ background-color: {styles.COLOR_BG}; color: {styles.COLOR_TEXT_MAIN}; border: none; padding: 5px; font-weight: bold; }}
            QTableWidget::item {{ padding: 10px; }}
        """)

        try:
            users = self.db.fetch_all("SELECT id, username, role FROM users")
            table.setRowCount(len(users))
            for i, u in enumerate(users):
                table.setItem(i, 0, QTableWidgetItem(u['username']))
                table.setItem(i, 1, QTableWidgetItem(u['role']))
                table.setItem(i, 2, QTableWidgetItem(str(u['id'])))
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")

        layout.addWidget(table)
        return widget

    def _create_admin_add_word_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        info = QLabel("Добавление нового слова в общий справочник")
        info.setStyleSheet(f"font-family: {styles.FONT_HEADER}; font-size: 18px; font-weight: bold;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        self.admin_input_word = QLineEdit()
        self.admin_input_word.setPlaceholderText("Иностранное слово")
        self.admin_input_word.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 10px; }}
        """)

        self.admin_input_trans = QLineEdit()
        self.admin_input_trans.setPlaceholderText("Транскрипция")
        self.admin_input_trans.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 10px; }}
        """)

        self.admin_input_ru = QLineEdit()
        self.admin_input_ru.setPlaceholderText("Перевод")
        self.admin_input_ru.setStyleSheet(f"""
            QLineEdit {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; padding: 10px; }}
        """)

        form.addRow("Слово:", self.admin_input_word)
        form.addRow("Транскрипция:", self.admin_input_trans)
        form.addRow("Перевод:", self.admin_input_ru)
        layout.addLayout(form)

        btn_save = QPushButton("Сохранить слово")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setFixedHeight(50)
        btn_save.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_SUCCESS}; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #1E6B31; }}
        """)
        btn_save.clicked.connect(self.save_word_from_admin)
        layout.addWidget(btn_save)
        layout.addStretch()

        return widget

    def save_word_from_admin(self):
        word = self.admin_input_word.text().strip()
        trans = self.admin_input_trans.text().strip()
        ru = self.admin_input_ru.text().strip()

        if not word or not ru:
            QMessageBox.warning(self, "Ошибка", "Слово и перевод обязательны!")
            return

        if not re.search(r'[a-zA-Zа-яА-Я]', word):
            QMessageBox.warning(self, "Ошибка", "Слово должно содержать буквы!")
            return

        try:
            query = "INSERT INTO words (foreign_word, translation, transcription, collection_id) VALUES (?, ?, ?, 1)"
            self.db.execute_query(query, (word, ru, trans))
            self.admin_input_word.clear()
            self.admin_input_trans.clear()
            self.admin_input_ru.clear()
            QMessageBox.information(self, "Успех", f"Слово '{word}' успешно добавлено!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))

    def _create_admin_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        info = QLabel("Управление данными и отчётность")
        info.setStyleSheet(f"font-family: {styles.FONT_HEADER}; font-size: 18px; font-weight: bold;")
        layout.addWidget(info)

        btn_export_csv = QPushButton("📥 Экспорт успеваемости в CSV")
        btn_export_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_csv.setFixedHeight(50)
        btn_export_csv.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_ACCENT}; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #4C6EF5; }}
        """)
        btn_export_csv.clicked.connect(self.export_report_csv)
        layout.addWidget(btn_export_csv)

        btn_backup = QPushButton("💾 Создать резервную копию БД")
        btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup.setFixedHeight(50)
        btn_backup.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_SUCCESS}; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #1E6B31; }}
        """)
        btn_backup.clicked.connect(self.create_backup)
        layout.addWidget(btn_backup)

        layout.addStretch()
        return widget

    def export_report_csv(self):
        try:
            filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(os.getcwd(), filename)

            rows = self.db.fetch_all("""
                SELECT u.username, w.foreign_word, r.quality, r.next_review_date 
                FROM reviews r 
                JOIN users u ON r.user_id = u.id 
                JOIN words w ON r.word_id = w.id
            """)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Пользователь', 'Слово', 'Оценка', 'Дата следующей проверки'])
                for row in rows:
                    writer.writerow([row['username'], row['foreign_word'], row['quality'], row['next_review_date']])

            QMessageBox.information(self, "Успех", f"Отчёт успешно сохранён:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать отчёт: {e}")

    def create_backup(self):
        try:
            db_path = None
            if hasattr(self.db, 'db_path'):
                db_path = self.db.db_path

            if not db_path or not os.path.exists(db_path):
                possible_paths = [
                    "worder.db", "words.db",
                    "database/worder.db", "database/words.db",
                    "db/worder.db", "db/words.db",
                    os.path.join(os.path.dirname(__file__), "worder.db"),
                    os.path.join(os.path.dirname(__file__), "words.db")
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        db_path = p
                        break

            if not db_path:
                raise FileNotFoundError("Файл базы данных не найден ни в одном из стандартных мест.")

            backup_dir = os.path.join(os.getcwd(), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")

            shutil.copy2(db_path, backup_path)
            QMessageBox.information(self, "Успех", f"Резервная копия создана:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать бэкап: {str(e)}")

    def create_about_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.create_header())

        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setContentsMargins(40, 20, 40, 20)

        btn_back = QPushButton("← На главную")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {styles.COLOR_TEXT_MUTED}; border: none; font-size: 14px; text-align: left; }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_back.clicked.connect(lambda: self.switch_screen(0))

        breadcrumbs = QLabel("Главная > О программе")
        breadcrumbs.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED};")

        breadcrumb_layout.addWidget(btn_back)
        breadcrumb_layout.addStretch()
        breadcrumb_layout.addWidget(breadcrumbs)
        layout.addLayout(breadcrumb_layout)

        about_container = QFrame()
        about_container.setStyleSheet(
            f"background-color: {styles.COLOR_SURFACE}; border-radius: 16px; border: 1px solid {styles.COLOR_BORDER}; margin: 40px;")
        about_layout = QVBoxLayout(about_container)
        about_layout.setContentsMargins(60, 60, 60, 60)
        about_layout.setSpacing(20)
        about_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Worder")
        title.setStyleSheet(
            f"font-family: {styles.FONT_HEADER}; font-size: 48px; font-weight: bold; color: {styles.COLOR_TEXT_MAIN};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(title)

        subtitle = QLabel("Тренажёр иностранных слов с интервальным повторением")
        subtitle.setStyleSheet(f"font-size: 18px; color: {styles.COLOR_TEXT_MUTED};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {styles.COLOR_BORDER}; max-height: 1px; margin: 20px 0;")
        about_layout.addWidget(divider)

        info_text = f"""
        <div style='text-align: center; font-size: 16px; line-height: 2.2; color: {styles.COLOR_TEXT_MAIN};'>
            <b>Разработчик:</b> Бокштай П.Е.<br>
            <b>Группа:</b> 22о<br>
            <b>Стек технологий:</b> Python 3.11, PyQt6, SQLite3, bcrypt<br>
            <b>Алгоритм повторения:</b> Упрощённый SM-2<br>
            <b>Версия:</b> 1.0.0
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(info_label)

        about_layout.addStretch()
        layout.addWidget(about_container, 1)
        layout.addWidget(self.create_footer())

        self.about_container = about_container
        return screen

    def update_table(self, table, word_list):
        table.setRowCount(len(word_list))
        for row, word in enumerate(word_list):
            item_word = QTableWidgetItem(word["word"])
            # Сохраняем ID внутри элемента таблицы для надежного удаления
            item_word.setData(Qt.ItemDataRole.UserRole, word["id"])
            item_word.setFlags(item_word.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, item_word)

            item_ru = QTableWidgetItem(word["ru"])
            item_ru.setFlags(item_ru.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 1, item_ru)

            item_trans = QTableWidgetItem(word["trans"])
            item_trans.setFlags(item_trans.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 2, item_trans)

            item_status = QTableWidgetItem(word["status"])
            item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 3, item_status)

    def filter_table(self, table, combo, is_personal, search_text=""):
        selected = combo.currentText()
        words = self.get_personal_words() if is_personal else self.get_all_words()

        if is_personal and selected != "Все мои слова":
            words = [w for w in words if w["status"] == selected]

        if search_text:
            search_lower = search_text.lower()
            words = [w for w in words if search_lower in w["word"].lower() or search_lower in w["ru"].lower()]

        self.update_table(table, words)

    def load_test_words(self):
        test_words = [
            (1, 'Apple', 'Яблоко', '[ˈæp.əl]', 1), (2, 'Bread', 'Хлеб', '[bred]', 1),
            (3, 'Cheese', 'Сыр', '[tʃiːz]', 1), (4, 'Water', 'Вода', '[ˈwɔːtər]', 1),
            (5, 'Meat', 'Мясо', '[miːt]', 1), (6, 'Airport', 'Аэропорт', '[ˈeəpɔːt]', 2),
            (7, 'Ticket', 'Билет', '[ˈtɪkɪt]', 2), (8, 'Luggage', 'Багаж', '[ˈlʌɡɪdʒ]', 2),
            (9, 'Passport', 'Паспорт', '[ˈpɑːspɔːt]', 2), (10, 'Hotel', 'Отель', '[həʊˈtel]', 2),
            (11, 'Train', 'Поезд', '[treɪn]', 2), (12, 'Car', 'Машина', '[kɑːr]', 2),
            (13, 'Road', 'Дорога', '[rəʊd]', 2), (14, 'City', 'Город', '[ˈsɪti]', 2),
            (15, 'Country', 'Страна', '[ˈkʌntri]', 2), (16, 'Friend', 'Друг', '[frend]', 2),
            (17, 'Family', 'Семья', '[ˈfæməli]', 2), (18, 'Work', 'Работа', '[wɜːrk]', 2),
            (19, 'Money', 'Деньги', '[ˈmʌni]', 2), (20, 'Time', 'Время', '[taɪm]', 2),
        ]
        try:
            for w in test_words:
                query = "INSERT OR IGNORE INTO words (id, foreign_word, translation, transcription, collection_id) VALUES (?, ?, ?, ?, ?)"
                self.db.execute_query(query, w)
            self.filter_table(self.all_table, self.all_combo, False)
            QMessageBox.information(self, "Успех", "Тестовые слова успешно добавлены в справочник.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить слова: {e}")

    def reset_progress(self):
        reply = QMessageBox.question(self, 'Сброс прогресса',
                                     'Удалить ВСЕ слова из вашего личного словаря и сбросить прогресс?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM reviews WHERE user_id = ?", (self.user_id,))
                self.filter_table(self.my_table, self.my_combo, True)
                self.update_dashboard_stats()
            except Exception as e:
                print(f"Ошибка сброса прогресса: {e}")

    def start_training(self):
        all_words = self.get_all_words()
        personal_words = self.get_personal_words()

        if not all_words:
            QMessageBox.warning(self, "Внимание", "Справочник пуст! Добавьте слова через админ-панель.")
            return

        finished_ids = {w["id"] for w in personal_words if w["status"] in ["Выучено", "Уже известно"]}
        words_to_learn = [w for w in all_words if w["id"] not in finished_ids]

        if not words_to_learn:
            reply = QMessageBox.question(
                self,
                "Обучение завершено",
                "Вы изучили все доступные слова из справочника!\n\nСбросить прогресс и начать заново?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.execute_query("DELETE FROM reviews WHERE user_id = ?", (self.user_id,))
                    words_to_learn = all_words
                    self.update_dashboard_stats()
                except Exception as e:
                    print(f"Ошибка сброса: {e}")
            else:
                return

        self.words = words_to_learn
        self.current_word_index = 0
        self.update_card()
        self.animate_card()
        self.switch_screen(1)

    def update_card(self):
        if not self.words: return
        word_data = self.words[self.current_word_index]
        self.lbl_ru.hide()
        self.lbl_word.setText(word_data["word"])
        self.lbl_transcription.setText(word_data["trans"])
        self.lbl_ru.setText(word_data["ru"])

    def animate_card(self):
        self.card.setWindowOpacity(0.0)

        self.fade_in = QPropertyAnimation(self.card, b"windowOpacity")
        self.fade_in.setDuration(400)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in.start()

    def create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(
            f"background-color: {styles.COLOR_SURFACE}; border-bottom: 1px solid {styles.COLOR_BORDER};")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel()
        logo.setText(
            f'<span style="color:{styles.COLOR_TEXT_MAIN}; font-family:{styles.FONT_HEADER}; font-size:20px; font-weight:bold;">Word</span>'
            f'<span style="color:{styles.COLOR_GREEN_ER}; font-family:{styles.FONT_HEADER}; font-size:20px; font-weight:bold;">er</span>')
        layout.addWidget(logo)

        layout.addStretch()

        btn_about = QPushButton("ℹ️ О программе")
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {styles.COLOR_TEXT_MUTED}; border: none; font-size: 14px; }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_about.clicked.connect(lambda: self.switch_screen(self.about_index))
        layout.addWidget(btn_about)

        user_label = QLabel(f"{self.username} ({self.role}) 👤")
        user_label.setStyleSheet(f"color: {styles.COLOR_TEXT_MAIN}; font-size: 14px; border: none;")

        btn_logout = QPushButton("Выйти")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {styles.COLOR_TEXT_MUTED}; border: 1px solid {styles.COLOR_TEXT_MUTED}; border-radius: 4px; padding: 5px 10px; }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; border-color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_logout.clicked.connect(self.logout)

        layout.addWidget(user_label)
        layout.addWidget(btn_logout)
        return header

    def create_menu_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {styles.COLOR_SURFACE}; color: {styles.COLOR_TEXT_MAIN}; border: 1px solid {styles.COLOR_BORDER}; border-radius: 8px; text-align: left; padding-left: 20px; font-size: 16px; }}
            QPushButton:hover {{ background-color: {styles.COLOR_ACCENT}; border-color: {styles.COLOR_ACCENT}; color: white; }}
            QPushButton:pressed {{ background-color: #2C4AB5; }}
        """)
        return btn

    def create_rating_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedSize(150, 50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {color}; border: 2px solid {color}; border-radius: 8px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {color}; color: white; }}
        """)
        return btn

    def create_footer(self):
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet(f"background-color: {styles.COLOR_SURFACE}; border-top: 1px solid {styles.COLOR_BORDER};")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 0, 20, 0)

        lbl_footer = QLabel("Worder © 2026 | Разработчик: Бокштай П.Е., группа 22о")
        lbl_footer.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED}; font-size: 12px; border: none;")

        layout.addWidget(lbl_footer)
        return footer

    def switch_screen(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index == 2:
            self.filter_table(self.my_table, self.my_combo, True)
        elif index == 3:
            self.filter_table(self.all_table, self.all_combo, False)
        elif index == self.about_index:
            self.animate_about()

    def animate_about(self):
        self.about_container.setWindowOpacity(0.0)

        self.fade_in_about = QPropertyAnimation(self.about_container, b"windowOpacity")
        self.fade_in_about.setDuration(500)
        self.fade_in_about.setStartValue(0.0)
        self.fade_in_about.setEndValue(1.0)
        self.fade_in_about.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in_about.start()

    def handle_answer(self, quality):
        if not self.words: return
        current_word = self.words[self.current_word_index]
        word_id = current_word["id"]

        try:
            check_query = "SELECT id FROM reviews WHERE word_id = ? AND user_id = ?"
            existing = self.db.fetch_all(check_query, (word_id, self.user_id))

            interval = 1 if quality < 3 else 3
            next_date = (datetime.datetime.now() + datetime.timedelta(days=interval)).strftime('%Y-%m-%d %H:%M:%S')

            if existing:
                update_query = "UPDATE reviews SET quality = ?, next_review_date = ?, interval_days = ? WHERE word_id = ? AND user_id = ?"
                self.db.execute_query(update_query, (quality, next_date, interval, word_id, self.user_id))
            else:
                insert_query = "INSERT INTO reviews (word_id, user_id, quality, next_review_date, interval_days) VALUES (?, ?, ?, ?, ?)"
                self.db.execute_query(insert_query, (word_id, self.user_id, quality, next_date, interval))
        except Exception as e:
            print(f"Ошибка записи в БД: {e}")

        self.current_word_index = (self.current_word_index + 1) % len(self.words)
        self.update_card()
        self.animate_card()
        self.update_dashboard_stats()

    def logout(self):
        self.hide()
        global_login_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    global_login_window = LoginWindow(WorderApp)
    global_login_window.show()
    sys.exit(app.exec())