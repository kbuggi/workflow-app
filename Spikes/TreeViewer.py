import sys
import json
import jsonc
import os
import re
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QTextEdit, QSplitter, QLabel, QFrame, QHeaderView, QMenu, QListWidget
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSettings


class JsonViewer(QMainWindow):
    def __init__(self):
        super(JsonViewer, self).__init__()

        self.setWindowTitle("JSON/JSONC Viewer")
        self.setGeometry(100, 100, 1600, 600)

        app.setWindowIcon(QIcon(os.path.abspath("json_icon.png")))

        layout = QVBoxLayout()

        topBar = QHBoxLayout()

        self.openButton = QPushButton("Open JSON/JSONC File")
        self.openButton.clicked.connect(self.open_file)
        topBar.addWidget(self.openButton)

        self.favoritesButton = QPushButton("Open Favorite File")
        self.favoritesButton.clicked.connect(self.open_favorite_file)
        topBar.addWidget(self.favoritesButton)

        self.pathLabel = QLabel("")
        self.pathLabel.setStyleSheet("background-color: black; color: white; padding: 4px;")
        self.pathLabel.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.pathLabel.setFixedHeight(30)
        self.pathLabel.setMinimumWidth(280)
        topBar.addWidget(self.pathLabel)

        layout.addLayout(topBar)

        self.splitter = QSplitter()

        self.treeWidgets = []
        self.open_columns = set()
        self.add_tree_widget()

        inspector_container = QVBoxLayout()

        self.keyLabel = QLabel("")
        self.keyLabel.setStyleSheet("background-color: black; color: white; text-align: center;")
        self.keyLabel.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.keyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inspector_container.addWidget(self.keyLabel)

        self.inspector = QTextEdit()
        self.inspector.setReadOnly(True)
        self.inspector.setStyleSheet("background-color: black; color: white;")
        inspector_container.addWidget(self.inspector)

        inspector_widget = QWidget()
        inspector_widget.setLayout(inspector_container)
        self.splitter.addWidget(inspector_widget)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.current_font_size = 12 #TODO load from QSettings
        self.set_font_size(self.current_font_size)

        #automagically load most recent file
        self.load_most_recent_file()

        self.highlight_pattern = re.compile(".*")

        self.favorites = self.load_favorites()

    def keyPressEvent(self, event):#watch out for Control+/Control-/Control=
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key()  in (Qt.Key.Key_Plus, Qt.Key.Key_Equal) ) or \
           (event.modifiers() & Qt.KeyboardModifier.MetaModifier and event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal) ):  # Control on Windows, Command on macOS
            print("Command+")
            self.current_font_size += 2
            self.set_font_size(self.current_font_size)

        elif (event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Minus) or \
             (event.modifiers() & Qt.KeyboardModifier.MetaModifier and event.key() == Qt.Key.Key_Minus):
            print("Command-")
            if self.current_font_size >= 8:  # Prevent font from getting too tiny
                self.current_font_size -= 2
                self.set_font_size(self.current_font_size)
        else:
            print( f"Other key '{event.key()}'")



    def set_font_size(self, size):
        font = QFont()
        font.setPointSize(size)
        for tree in self.treeWidgets:
            tree.setFont(font)
        self.inspector.setFont(font)
        self.keyLabel.setFont(font)
        self.pathLabel.setFont(font)

    def open_file(self):
            file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON/JSONC File", "", "JSON Files (*.json *.jsonc);;All Files (*)")        
            if file_name:
                self.load_file(file_name)
                self.add_to_favorites(file_name)

    def load_file(self, file_name):
        try:
            with open(file_name, "r") as file:
                if file_name.endswith(".jsonc"):
                    data = jsonc.load(file)
                else:
                    data = json.load(file)
                self.display_json(data, self.treeWidgets[0])
                self.pathLabel.setText(file_name)
                self.save_most_recent_filename(file_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")

    def load_most_recent_file(self):
        filename = self.load_most_recent_filename()
        if not filename:
            print("No recent file")
            return
        self.load_file(filename)

    def load_most_recent_filename(self):
        settings = QSettings("Katalina", "TreeViewerApp")
        filename = settings.value("most_recent_file", "")
        return filename

    def save_most_recent_filename(self, filename):
        settings = QSettings("Katalina", "TreeViewerApp")
        settings.setValue("most_recent_file", filename)



    def open_favorite_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Favorite File", "", "\n".join(self.favorites))
        if file_name:
            self.load_file(file_name)

    def add_to_favorites(self, file_name):
        if file_name not in self.favorites:
            self.favorites.append(file_name)
            self.save_favorites()

    def load_favorites(self):
        try:
            with open(".json_favorites", "r") as file:
                return file.read().splitlines()
        except Exception:
            return []

    def save_favorites(self):
        try:
            with open(".json_favorites", "w") as file:
                file.write("\n".join(self.favorites))
        except Exception:
            pass

    def add_tree_widget(self):
        if len(self.treeWidgets) >= 3:
            return

        treeWidget = QTreeWidget()
        treeWidget.setHeaderLabels(["Key", "Value"])
        treeWidget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        treeWidget.setColumnWidth(0, 280)
        treeWidget.itemClicked.connect(self.update_inspector)
        #treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        #treeWidget.customContextMenuRequested.connect(lambda point, tw=treeWidget: self.open_context_menu(point, tw))

        self.treeWidgets.append(treeWidget)
        self.splitter.insertWidget(len(self.treeWidgets) - 1, treeWidget)
        
        
    def display_json(self, data, parent):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent, [str(key), ""] if isinstance(value, (dict, list)) else [str(key), str(value)])
                item.setData(0, 1, value)
                self.display_json(value, item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem(parent, [f"[{index}]", ""] if isinstance(value, (dict, list)) else [f"[{index}]", str(value)])
                item.setData(0, 1, value)
                self.display_json(value, item)

    def update_inspector(self, item):
        key = item.text(0)
        data = item.data(0, 1)

        self.keyLabel.setText(key)

        try:
            if isinstance(data, dict):
                pretty_json = jsonc.dumps(data, indent=4)
                self.inspector.setPlainText(pretty_json)
            elif isinstance(data, list):
                pretty_json = json.dumps(data, indent=4)
                self.inspector.setPlainText(pretty_json)
            else:
                self.inspector.setPlainText(str(data))
        except Exception as e:
            self.inspector.setPlainText(f"Error displaying data: {str(e)}")

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = JsonViewer()
    viewer.show()
    sys.exit(app.exec())
