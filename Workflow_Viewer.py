f"if this is python 2.x you will get a syntax error here"
import assert_environment

import logging

import sys, os

import json, jsonc, argparse, datetime, subprocess

from Workflow_Model import WorkflowStream, Stream, Task

from GitSync import GitSyncThread

from config import Config

from GridUI import GridController

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QProcess


# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class WorkflowViewer(QMainWindow):
    def __init__(self, filename=None):
        super(WorkflowViewer, self).__init__()
        self.processes = []
        self.w = None
        self.filename = None
        self.controller = None
        self.central = QWidget()
        self.main_layout = QVBoxLayout(self.central)

        button_layout = QHBoxLayout()
        self.open_button = QPushButton("📂 Open recipe")
        self.open_button.clicked.connect(self.open_file_dialog)
        button_layout.addWidget(self.open_button)

        self.sync_button = QPushButton("▶🔁  Sync recipes")
        self.sync_button.clicked.connect(self.sync_recipes)
        button_layout.addWidget(self.sync_button)

        self.media_button = QPushButton("▶️  Play recipe media")
        self.media_button.clicked.connect(self.play_media)
        button_layout.addWidget(self.media_button)

        self.start_button = QPushButton("➡️  Start recipe")
        self.start_button.clicked.connect(self.start_recipe)
        button_layout.addWidget(self.start_button)
        self.main_layout.addLayout(button_layout)
        self.setLayout(self.main_layout)
        self.setCentralWidget(self.central)
        # Create Statusbar
        # self.status = self.statusBar()

        if filename:
            self.load_file(filename)
        else:
            self.load_most_recent_file()

    def on_process_finished(self, process, exitCode, exitStatus):
        self.showFullScreen()
        logger.info(f"Sub-process {process} exited with code {exitCode}")
        self.processes.remove(process)
        if self.isMinimized():
            self.showNormal()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def start_media_player(self):
        process = QProcess()
        process.finished.connect(
            lambda code, status, p=process: self.on_process_finished(p, code, status)
        )

        python = sys.executable
        code = Config.CODE_SLIDESHOW
        if not self.w.media_file:
            QMessageBox.critical(
                None,
                "Error",
                "No media available for this recipe",
                QMessageBox.StandardButton.Ok,
            )

            return
        media_file = self.w.media_file

        #
        # python Media_Player.py --file /Users/katalina/Library/KatalinaM/WorkflowApp/RecipeCache/recipes/recipe-eggs-and-soldiers-final.media.json --path /Users/katalina/Library/KatalinaM/WorkflowApp/RecipeCache/media
        media_file = os.path.join(Config.USER_RECIPE_CACHE_SUBFOLDER, media_file)
        if not os.path.exists(media_file):
            QMessageBox.critical(
                None,
                "Error",
                f"Media file {media_file} does not exist",
                QMessageBox.StandardButton.Ok,
            )
            return
        args = [
            code,
            "--file",
            media_file,
            "--path",
            Config.USER_RECIPE_CACHE_MEDIAFOLDER,
        ]
        logger.info(f"Starting media_file {media_file} ...")
        logger.info(args)
        process.start(python, args)
        logger.info(f"media started in Sub-process {process} ")
        self.processes.append(process)

    def start_workflow_engine(self):
        process = QProcess()
        process.finished.connect(
            lambda code, status, p=process: self.on_process_finished(p, code, status)
        )

        python = sys.executable
        code = Config.CODE_ENGINE

        workflow_file = self.filename

        args = [code, workflow_file]
        logger.info(f"Starting workflow {workflow_file} ...")

        process.start(python, args)
        logger.info(f"workflow started in Sub-process {process} ")
        self.processes.append(process)

    def play_media(self):
        logger.debug("play_media button pressed")
        self.start_media_player()

    def start_recipe(self):
        logger.debug("start_recipe button pressed")
        self.start_workflow_engine()

    def sync_recipes(self):
        self.config_folder = Config.USER_RECIPE_CACHE_FOLDER
        self.repo_url = Config.REPO_URL  # URL of the Git repository

        logger.debug("sync_recipes button pressed")
        logger.info(f"Syncing recipes to {Config.USER_RECIPE_CACHE_FOLDER}")
        self.git_thread = GitSyncThread(self.repo_url, self.config_folder)
        self.git_thread.update_signal.connect(self.update_sync_status)
        self.git_thread.start()

    def update_sync_status(self, message):
        """Update the status label with messages from the background thread."""
        # self.status_label.setText(f"Status: {message}")
        logger.info(f"Sync Status: {message}")

    def load_most_recent_file(self):
        filename = self.get_most_recent_filename()
        if filename:
            self.load_file(filename)
        else:
            self.open_file_dialog()

    def open_file_dialog(self):
        folder = Config.USER_RECIPE_CACHE_FOLDER
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Recipe", folder, "JSON Files (*.json *.jsonc);;All Files (*)"
        )
        if filename:
            self.load_file(filename)

    def get_most_recent_filename(self):
        settings = QSettings("KatalinaM", "WorkflowApp")
        filename = settings.value("most_recent_file", "")
        return filename

    def save_most_recent_filename(self, filename):
        settings = QSettings("KatalinaM", "WorkflowApp")
        settings.setValue("most_recent_file", filename)

    def populate_controller(self):
        # self.w holds workflow

        for type_string, name, column, row, reference in self.w.iterator_visualiser():
            logger.info(
                f"viz: type_string:{type_string} name:{name} column:{column} row:{row}"
            )
            # set defaults for each cell; type-specific settings will override
            width = 1
            text_colour = Qt.GlobalColor.black
            if hasattr(reference, "title") and reference.title != "":
                label = reference.title
            else:
                label = name
            if hasattr(reference, "dictionary"):
                dictionary = reference.dictionary
            else:
                dictionary = {}
            if type_string == "Stream":
                dictionary = {"Stream": name}
                background_colour = Qt.GlobalColor.darkMagenta
            # User suggestion : show more about task in the viewer
            elif type_string == "Task":
                if reference.type == "Active":
                    background_colour = Qt.GlobalColor.white
                else:
                    background_colour = Qt.GlobalColor.darkGray
                if reference.Autoprogress:
                    label += ""  # TODO - pick an emoji
                if reference.CheckMessage or reference.StartMessage:
                    label += " ‼️"  # indicates speech
            elif type_string == "PrePostStream":
                background_colour = Qt.GlobalColor.darkCyan
                text_colour = Qt.GlobalColor.white
                width = 3
            elif type_string == "Trigger":
                background_colour = Qt.GlobalColor.black
                label = "↘️"
                dictionary = {"trigger": name}
            else:
                logger.error(
                    f"Unknown type: '{type_string}' for workflow item '{name}'; unable to visualize it properly"
                )

            self.controller.populate_cell(
                column, row, width, text_colour, background_colour, label, dictionary
            )

        # self.controller.reset_window_height() # resize window to show all rows (if possible)

    def load_file(self, filename):
        logger.info(f"Opening workstream recipe filename {filename}")
        if self.controller:
            self.controller.setParent(None)  # Remove the widget from the layout
            del self.controller
            self.controller = None
        if self.w:
            del self.w
            self.w = None
        try:
            with open(filename, "r") as file:
                recipe_dict = jsonc.load(file)
            w = WorkflowStream(filename, recipe_dict)
            logger.info(f" opened workstream {w.name} ")
            warnings = w.build()
            if warnings:
                msg = "\n".join(warnings)
                QMessageBox.critical(
                    self, "Build warnings", msg, QMessageBox.StandardButton.Ok
                )
                logger.error(f"Warnings building recipe from {filename}: {msg}")
            logger.info("Loaded workstream {self.w.name} from filename {filename} ")

        except OSError as e:
            msg = f"Uable to open Workflow file {filename}:\n{e}"
            logger.error(msg)
            QMessageBox.critical(self, "Error", msg, QMessageBox.StandardButton.Ok)
        except json.decoder.JSONDecodeError as e:
            msg = f"Uable to interpret Workflow file {filename}:\n{e}"
            QMessageBox.critical(self, "Error", msg, QMessageBox.StandardButton.Ok)
        self.w = w
        self.save_most_recent_filename(filename)
        self.setWindowTitle(self.w.name)

        self.filename = filename
        self.controller = GridController(self.w.name)
        self.main_layout.addWidget(self.controller)
        self.populate_controller()
        # self.controller.show()
        # self.main_layout.addWidget(self.controller)
        # TODO - change title bar


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Views a workflow (typically a recipe) as part of the workflow ecosystem"
    )
    # Define arguments
    parser.add_argument(
        "--filename",
        default=None,
        help="recipe/workflow in json/jsonc format (last will be opened if none provided)",
    )
    args = parser.parse_args()

    print("Starting application...")
    app = QApplication(sys.argv)

    window = WorkflowViewer(args.filename)
    # User feedback change -  Start the application in fullscreen mode
    window.showFullScreen()

    sys.exit(app.exec())
