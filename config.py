from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize
from pathlib import Path
import os, platform, sys


class Config:
    # Recipe path
    REPO_URL = "https://github.com/kbuggi/Resources"
    os_name = platform.system().lower()
    USER_RECIPE_CACHE_FOLDER = str(
        Path.home() / "Library" / "KatalinaM" / "WorkflowApp" / "RecipeCache"
    )
    USER_RECIPE_CACHE_SUBFOLDER = f"{USER_RECIPE_CACHE_FOLDER}/recipes"
    USER_RECIPE_CACHE_MEDIAFOLDER = f"{USER_RECIPE_CACHE_FOLDER}/media"

    # In case os specific settings are needed
    if os_name == "darwin":  # macOS
        pass
    elif os_name == "windows":  # Windows
        pass
    else:
        pass

    # Resource paths
    RESOURCE_PATH = "resources"
    CODE_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
    ICONS_PATH = f"{RESOURCE_PATH}/icons"
    AUDIO_PATH = f"{RESOURCE_PATH}/audio"
    JSON_PATH = f"{RESOURCE_PATH}/json"
    SAMPLE_RECIPE_FOLDER_PATH = RESOURCE_PATH + "/sample_recipes"
    SAMPLE_RECIPE_PATH = SAMPLE_RECIPE_FOLDER_PATH + "/recipe-simple.jsonc"

    CODE_SLIDESHOW = os.path.join(CODE_PATH, "Media_Player.py")
    CODE_ENGINE = os.path.join(CODE_PATH, "Workflow_Engine.py")
    JSON_SCHEMA_DOWNLOAD_RECIPE = os.path.join(JSON_PATH, "standard-recipe-schema.json")

    # Icons from https://fontawesome.com
    ICON_DELETE = QIcon(f"{ICONS_PATH}/circle-xmark-solid.svg")
    ICON_PAUSE = QIcon(f"{ICONS_PATH}/pause-solid.svg")
    ICON_RESUME = QIcon(f"{ICONS_PATH}/play-solid.svg")
    ICON_EXTEND = QIcon(f"{ICONS_PATH}/plus-solid.svg")
    ICON_REDUCE = QIcon(f"{ICONS_PATH}/minus-solid.svg")
    ICON_DONE = QIcon(f"{ICONS_PATH}/forward-solid.svg")
    ICON_BACK = QIcon(f"{ICONS_PATH}/backward-solid.svg")

    # Icon sizes
    ICON_SIZE_SMALL = QSize(24, 24)
    ICON_SIZE_MEDIUM = QSize(32, 32)

    # Fonts
    TITLE_FONT = QFont("Arial", 16)
    DESCRIPTION_FONT = QFont("Arial", 18)
    TIMER_FONT = QFont("Arial", 30)
    BUTTON_FONT = QFont("Arial", 20)

    # Colors
    # TODO change disabled colour to darkgrey
    # also change flight checklists to grey or lightgrey
    BG_COLOR = "DarkGrey"
    ACTIVE_BG_COLOR = "White"
    TIMER_BG_COLORS = {
        "red": "red",
        "amber": "yellow",
        "green": "lightgreen",
        "default": "lightgrey",
    }
    BUTTON_ENABLED_COLOR = "white"
    BUTTON_DISABLED_COLOR = "DarkGrey"

    # Layout settings
    LAYOUT_SPACING = 5
    LAYOUT_MARGINS = (5, 5, 5, 5)
