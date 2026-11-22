import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt
import styles


class WorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Worder — Тренажёр иностранных слов")
        self.setMinimumSize(1024, 768)

        self.setStyleSheet(styles.MAIN_STYLE)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. ШАПКА
        main_layout.addWidget(self.create_header())

        # 2. ОСНОВНАЯ ОБЛАСТЬ
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(40)

        # Левая колонка (Меню)
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        btn_review = self.create_menu_button("↻ К повторению сегодня")
        btn_learn = self.create_menu_button("+ Учить новые слова")
        btn_browse = self.create_menu_button("⤨ Пролистать слова")

        left_column.addWidget(btn_review)
        left_column.addWidget(btn_learn)
        left_column.addWidget(btn_browse)
        left_column.addStretch()

        # Правая колонка (Статистика)
        right_column = QVBoxLayout()
        right_column.setSpacing(20)

        stats_panel = QFrame()
        stats_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLOR_SURFACE};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {styles.COLOR_BORDER};
            }}
        """)
        stats_layout = QVBoxLayout(stats_panel)

        lbl_stats_title = QLabel("Статистика за неделю")
        lbl_stats_title.setStyleSheet(f"color: {styles.COLOR_TEXT_MUTED}; font-size: 14px; border: none;")

        lbl_stats_words = QLabel("Изучено слов: 48")
        lbl_stats_words.setStyleSheet(
            f"color: {styles.COLOR_TEXT_MAIN}; font-family: {styles.FONT_HEADER}; font-size: 24px; font-weight: bold; border: none;")

        lbl_stats_streak = QLabel("Серия: 5 дней")
        lbl_stats_streak.setStyleSheet(f"color: {styles.COLOR_TEXT_MAIN}; font-size: 16px; border: none;")

        stats_layout.addWidget(lbl_stats_title)
        stats_layout.addWidget(lbl_stats_words)
        stats_layout.addWidget(lbl_stats_streak)
        stats_layout.addStretch()

        right_column.addWidget(stats_panel)
        right_column.addStretch()

        content_layout.addLayout(left_column, 1)
        content_layout.addLayout(right_column, 2)

        main_layout.addWidget(content_area, 1)

        # 3. ПОДВАЛ
        main_layout.addWidget(self.create_footer())

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorderApp()
    window.show()
    sys.exit(app.exec())