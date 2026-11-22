COLOR_BG = "#1E1E24"
COLOR_SURFACE = "#2B2D35"
COLOR_TEXT_MAIN = "#E9ECEF"
COLOR_TEXT_MUTED = "#868E96"
COLOR_ACCENT = "#3B5BDB"
COLOR_SUCCESS = "#2B8A3E"
COLOR_DANGER = "#C92A2A"
COLOR_GREEN_ER = "#B6D7A8"
COLOR_BORDER = "#3E414A"

FONT_HEADER = "Montserrat, sans-serif"
FONT_MAIN = "Inter, sans-serif"

MAIN_STYLE = f"""
    QMainWindow {{
        background-color: {COLOR_BG};
    }}
    QWidget {{
        font-family: {FONT_MAIN};
        color: {COLOR_TEXT_MAIN};
    }}
    QLabel {{
        color: {COLOR_TEXT_MAIN};
    }}
"""