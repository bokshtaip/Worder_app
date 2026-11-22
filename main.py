import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame,
                             QStackedWidget, QStackedLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
import styles
from database.db_manager import DatabaseManager
import datetime


class AnimatedBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def animate(self):
        self.offset += 0.005
        if self.offset > 1.0:
            self.offset = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(styles.COLOR_BG))
        gradient.setColorAt(self.offset, QColor(styles.COLOR_SURFACE))
        gradient.setColorAt(1, QColor(styles.COLOR_BG))
        painter.fillRect(self.rect(), gradient)


class WorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Worder — Тренажёр иностранных слов")
        self.setMinimumSize(1024, 768)
        self.setStyleSheet(styles.MAIN_STYLE)

        self.db = DatabaseManager()
        self.db.connect()
        self.db.init_db()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.dashboard_screen = self.create_dashboard()
        self.training_screen = self.create_training_screen()
        self.my_dict_screen = self.create_dict_screen(is_personal=True)
        self.all_words_screen = self.create_dict_screen(is_personal=False)

        self.stacked_widget.addWidget(self.dashboard_screen)
        self.stacked_widget.addWidget(self.training_screen)
        self.stacked_widget.addWidget(self.my_dict_screen)
        self.stacked_widget.addWidget(self.all_words_screen)

        self.stacked_widget.setCurrentIndex(0)

    def get_personal_words(self):
        try:
            query = """
                SELECT w.id, w.foreign_word, w.translation, w.transcription,
                       r.quality
                FROM words w
                JOIN reviews r ON w.id = r.word_id AND r.user_id = 2
            """
            rows = self.db.fetch_all(query)
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
                    "id": row["id"],
                    "word": row["foreign_word"],
                    "trans": row["transcription"] or "",
                    "ru": row["translation"],
                    "status": status
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
                    "id": row["id"],
                    "word": row["foreign_word"],
                    "trans": row["transcription"] or "",
                    "ru": row["translation"],
                    "status": "В справочнике"
                })
            return words
        except Exception as e:
            print(f"Ошибка загрузки справочника: {e}")
            return []

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

        lbl_stats_words = QLabel("Изучено слов: 48")
        lbl_stats_words.setStyleSheet(
            f"color: {styles.COLOR_TEXT_MAIN}; font-family: {styles.FONT_HEADER}; font-size: 24px; font-weight: bold;")

        stats_layout.addWidget(lbl_stats_title)
        stats_layout.addWidget(lbl_stats_words)
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
            QPushButton {{
                background-color: transparent;
                color: {styles.COLOR_TEXT_MUTED};
                border: none;
                font-size: 14px;
                text-align: left;
            }}
            QPushButton:hover {{ color: {styles.COLOR_TEXT_MAIN}; }}
        """)
        btn_back.clicked.connect(lambda: self.switch_screen(0))

        breadcrumbs = QLabel("Главная > Тренировка")
        breadcrumbs.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED};")

        breadcrumb_layout.addWidget(btn_back)
        breadcrumb_layout.addStretch()
        breadcrumb_layout.addWidget(breadcrumbs)
        layout.addLayout(breadcrumb_layout)

        center_area = QVBoxLayout()
        center_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(500, 300)
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLOR_SURFACE};
                border-radius: 16px;
                border: 1px solid {styles.COLOR_BORDER};
            }}
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
            QPushButton {{
                background-color: {styles.COLOR_ACCENT};
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
                margin-top: 20px;
            }}
            QPushButton:hover {{ background-color: #4C6EF5; }}
        """)
        btn_show.clicked.connect(lambda: self.lbl_ru.show())

        card_layout.addWidget(self.lbl_word)
        card_layout.addWidget(self.lbl_transcription)
        card_layout.addWidget(self.lbl_ru)
        card_layout.addWidget(btn_show)

        center_area.addWidget(self.card)

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

        center_area.addLayout(self.rating_layout)

        layout.addLayout(center_area, 1)

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
            QPushButton {{
                background-color: transparent;
                color: {styles.COLOR_TEXT_MUTED};
                border: none;
                font-size: 14px;
                text-align: left;
            }}
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
            QComboBox {{
                background-color: {styles.COLOR_SURFACE};
                color: {styles.COLOR_TEXT_MAIN};
                border: 1px solid {styles.COLOR_BORDER};
                border-radius: 4px;
                padding: 5px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {styles.COLOR_SURFACE};
                color: {styles.COLOR_TEXT_MAIN};
                selection-background-color: {styles.COLOR_ACCENT};
            }}
        """)

        filter_layout.addWidget(lbl_filter)
        filter_layout.addWidget(combo_filter)

        if is_personal:
            btn_reset = QPushButton("Сбросить прогресс")
            btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reset.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.COLOR_ACCENT};
                    color: white;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #2C4AB5; }}
            """)
            btn_reset.clicked.connect(self.reset_progress)
            filter_layout.addWidget(btn_reset)
        else:
            btn_load_test = QPushButton("Загрузить тестовые слова")
            btn_load_test.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_load_test.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles.COLOR_SUCCESS};
                    color: white;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                }}
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
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {styles.COLOR_SURFACE};
                color: {styles.COLOR_TEXT_MAIN};
                border: 1px solid {styles.COLOR_BORDER};
                border-radius: 8px;
                gridline-color: {styles.COLOR_BORDER};
                margin: 0 40px 20px 40px;
            }}
            QHeaderView::section {{
                background-color: {styles.COLOR_BG};
                color: {styles.COLOR_TEXT_MAIN};
                border: none;
                padding: 5px;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 10px;
            }}
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

    def update_table(self, table, word_list):
        table.setRowCount(len(word_list))
        for row, word in enumerate(word_list):
            item_word = QTableWidgetItem(word["word"])
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

    def filter_table(self, table, combo, is_personal):
        selected = combo.currentText()
        if is_personal:
            words = self.get_personal_words()
            if selected != "Все мои слова":
                words = [w for w in words if w["status"] == selected]
            self.update_table(table, words)
        else:
            self.update_table(table, self.get_all_words())

    def load_test_words(self):
        test_words = [
            (1, 'Apple', 'Яблоко', '[ˈæp.əl]', 1),
            (2, 'Bread', 'Хлеб', '[bred]', 1),
            (3, 'Cheese', 'Сыр', '[tʃiːz]', 1),
            (4, 'Water', 'Вода', '[ˈwɔːtər]', 1),
            (5, 'Meat', 'Мясо', '[miːt]', 1),
            (6, 'Airport', 'Аэропорт', '[ˈeəpɔːt]', 2),
            (7, 'Ticket', 'Билет', '[ˈtɪkɪt]', 2),
            (8, 'Luggage', 'Багаж', '[ˈlʌɡɪdʒ]', 2),
            (9, 'Passport', 'Паспорт', '[ˈpɑːspɔːt]', 2),
            (10, 'Hotel', 'Отель', '[həʊˈtel]', 2),
            (11, 'Train', 'Поезд', '[treɪn]', 2),
            (12, 'Car', 'Машина', '[kɑːr]', 2),
            (13, 'Road', 'Дорога', '[rəʊd]', 2),
            (14, 'City', 'Город', '[ˈsɪti]', 2),
            (15, 'Country', 'Страна', '[ˈkʌntri]', 2),
            (16, 'Friend', 'Друг', '[frend]', 2),
            (17, 'Family', 'Семья', '[ˈfæməli]', 2),
            (18, 'Work', 'Работа', '[wɜːrk]', 2),
            (19, 'Money', 'Деньги', '[ˈmʌni]', 2),
            (20, 'Time', 'Время', '[taɪm]', 2),
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
                self.db.execute_query("DELETE FROM reviews")
                self.filter_table(self.my_table, self.my_combo, True)
                print("Прогресс успешно сброшен.")
            except Exception as e:
                print(f"Ошибка сброса прогресса: {e}")

    def start_training(self):
        all_words = self.get_all_words()
        personal_words = self.get_personal_words()

        personal_ids = {w["id"] for w in personal_words}
        words_to_learn = [w for w in all_words if w["id"] not in personal_ids]

        if not words_to_learn:
            QMessageBox.information(self, "Обучение завершено", "Вы изучили все доступные слова из справочника!")
            return

        self.words = words_to_learn
        self.current_word_index = 0
        self.update_card()
        self.switch_screen(1)

    def update_card(self):
        if not self.words:
            return
        word_data = self.words[self.current_word_index]
        self.lbl_ru.hide()
        self.lbl_word.setText(word_data["word"])
        self.lbl_transcription.setText(word_data["trans"])
        self.lbl_ru.setText(word_data["ru"])

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

        user_label = QLabel("User 👤")
        user_label.setStyleSheet(f"color: {styles.COLOR_TEXT_MAIN}; font-size: 14px; border: none;")

        btn_logout = QPushButton("Выйти")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {styles.COLOR_TEXT_MUTED};
                border: 1px solid {styles.COLOR_TEXT_MUTED};
                border-radius: 4px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                color: {styles.COLOR_TEXT_MAIN};
                border-color: {styles.COLOR_TEXT_MAIN};
            }}
        """)

        layout.addWidget(user_label)
        layout.addWidget(btn_logout)
        return header

    def create_menu_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.COLOR_SURFACE};
                color: {styles.COLOR_TEXT_MAIN};
                border: 1px solid {styles.COLOR_BORDER};
                border-radius: 8px;
                text-align: left;
                padding-left: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {styles.COLOR_ACCENT};
                border-color: {styles.COLOR_ACCENT};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #2C4AB5;
            }}
        """)
        return btn

    def create_rating_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedSize(150, 50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
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

    def handle_answer(self, quality):
        if not self.words:
            return

        current_word = self.words[self.current_word_index]
        word_id = current_word["id"]

        try:
            check_query = "SELECT id FROM reviews WHERE word_id = ? AND user_id = 2"
            existing = self.db.fetch_all(check_query, (word_id,))

            interval = 1 if quality < 3 else 3
            next_date = (datetime.datetime.now() + datetime.timedelta(days=interval)).strftime('%Y-%m-%d %H:%M:%S')

            if existing:
                update_query = """
                    UPDATE reviews 
                    SET quality = ?, next_review_date = ?, interval_days = ?
                    WHERE word_id = ? AND user_id = 2
                """
                self.db.execute_query(update_query, (quality, next_date, interval, word_id))
            else:
                insert_query = """
                    INSERT INTO reviews (word_id, user_id, quality, next_review_date, interval_days)
                    VALUES (?, ?, ?, ?, ?)
                """
                self.db.execute_query(insert_query, (word_id, 2, quality, next_date, interval))

        except Exception as e:
            print(f"Ошибка записи в БД: {e}")

        self.current_word_index = (self.current_word_index + 1) % len(self.words)
        self.update_card()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorderApp()
    window.show()
    sys.exit(app.exec())