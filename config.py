from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize

class Config:
    # Resource paths
    RESOURCE_PATH = "resources"
    ICONS_PATH = f"{RESOURCE_PATH}/icons"
    AUDIO_PATH = f"{RESOURCE_PATH}/audio"

    # Icons
    ICON_DELETE = QIcon(f"{ICONS_PATH}/circle-xmark-solid.svg")
    ICON_PAUSE = QIcon(f"{ICONS_PATH}/pause-icon.svg")  # Example for pause icon
    ICON_RESUME = QIcon(f"{ICONS_PATH}/play-icon.svg")  # Example for resume icon

    # Icon sizes
    ICON_SIZE_SMALL = QSize(24, 24)
    ICON_SIZE_MEDIUM = QSize(32, 32)

    # Fonts
    TITLE_FONT = QFont("Arial", 16)
    DESCRIPTION_FONT = QFont("Arial", 18)
    TIMER_FONT = QFont("Arial", 30)
    BUTTON_FONT = QFont("Arial", 20)

    # Colors
    BG_COLOR = "DarkGrey"
    ACTIVE_BG_COLOR = "White"
    TIMER_BG_COLORS = {
        "red": "red",
        "amber": "yellow",
        "green": "lightgreen",
        "default": "lightgrey",
    }

    # Layout settings
    LAYOUT_SPACING = 5
    LAYOUT_MARGINS = (5, 5, 5, 5)