import json, jsonc
import time
##########

from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QFrame
from PyQt6.QtGui import QBrush, QPen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextOption

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem



import sys
import os

import re

# Regex pattern to match emojis
emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Symbols & pictographs
    "\U0001F680-\U0001F6FF"  # Transport & map symbols
    "\U0001F700-\U0001F77F"  # Alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric shapes
    "\U0001F800-\U0001F8FF"  # Supplemental arrows
    "\U0001F900-\U0001F9FF"  # Supplemental symbols & pictographs
    "\U0001FA00-\U0001FA6F"  # Chess symbols, etc.
    "\U0001FA70-\U0001FAFF"  # Symbols & pictographs extended
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "]+",
    flags=re.UNICODE
)

# Function to check if a string contains emojis
def contains_emoji(text):
    return bool(emoji_pattern.search(text))

def all_emoji(text):
    return bool(emoji_pattern.fullmatch(text))

CELL_WIDTH = 200
CELL_HEIGHT = 50
CELL_GAP = 10 


class GridCell(QGraphicsRectItem):


    def __init__(self, column, row, width, text_colour, background_colour, label, data, inspector_callback):
        self.CELL_WIDTH = CELL_WIDTH
        self.CELL_HEIGHT = CELL_HEIGHT
        self.CELL_GAP = CELL_GAP
        # Adjust position to include gaps only for distinct cells, not merged cells
        x_pos = column * (self.CELL_WIDTH + self.CELL_GAP)
        y_pos = row * (self.CELL_HEIGHT + self.CELL_GAP)

        # Calculate adjusted width: if the cell spans multiple columns, include gaps between them
        if width > 1:
            adjusted_width = (width * self.CELL_WIDTH) + ((width - 1) * self.CELL_GAP)
        else:
            adjusted_width = self.CELL_WIDTH

        super().__init__(0, 0, adjusted_width, self.CELL_HEIGHT)
        self.setBrush(QBrush(background_colour))
        self.setPen(QPen(Qt.GlobalColor.black))

        self.label = label
        self.data = data
        self.inspector_callback = inspector_callback

        # Center the text inside the cell
        text_item = QGraphicsTextItem(label, self)
        if contains_emoji(label) and len(label)<4: #left align & bottom align an individual emoji; bump fontsize
            font = QFont("Arial", 24) 
            text_item.setFont(font)
            text_item.setPos( 0  , 18) 
        else:
            font = QFont("Arial", 18)
            text_item.setFont(font)
            #word wrap any single cells.
            if width == 1:
                text_item.setTextWidth(self.CELL_WIDTH - 10) #forces word wrap
                text_item.adjustSize
            text_item.setX(10)
            text_item.setY( (self.CELL_HEIGHT - text_item.boundingRect().height()) / 2)
            #text_item.setPos((adjusted_width - text_item.boundingRect().width()) / 2, (self.CELL_HEIGHT - text_item.boundingRect().height()) / 2)
        text_item.setDefaultTextColor(text_colour)
        text_item.setParentItem(self)



        # Move the whole cell to its grid position
        self.setPos(x_pos, y_pos)

    def mousePressEvent(self, event):
        if self.inspector_callback:
            self.inspector_callback(self.label, self.data)
        super().mousePressEvent(event)


class InspectorPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)

        self.layout = QVBoxLayout()
        self.label = QLabel("Select a cell")
        font = QFont("Arial", 12)  # 'Arial' font, size 12
        self.label.setFont(font)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Value"])

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

    def update(self, label, data):
        self.label.setText(f"Label: {label}")
        if contains_emoji(label):
            font = QFont("Apple Color Emoji", 12)  # macOS example
        else:
            font = QFont("Arial", 12)  # 'Arial' font, size 12
        self.label.setFont(font)
            
        self.tree.clear()
        self.tree.setHeaderLabels(["Key", "Value"])

        if data is None or len(data)==0:
            data = {"Empty" : "[No data to display]"}
        for key, value in data.items():
            if isinstance(value, dict):  # Expand dictionary as level 1
                parent = QTreeWidgetItem(self.tree, [str(key), ""])
                parent.setForeground(0, Qt.GlobalColor.red)  # Set colour of level 1 key for visibility
                parent.setExpanded(True)  

                for sub_key, sub_value in value.items():  # Level 2
                    if isinstance(sub_key, list):  # Expand list as level 3
                        child=QTreeWidgetItem(parent, [str(key), ""])
                        child.setForeground(0, Qt.GlobalColor.darkMagenta)  
                        child.setExpanded(True)  
                        for index, item in enumerate(sub_value):  # Level 3
                            grandchild = QTreeWidgetItem(child, [str(index + 1), str(item)])
                            grandchild.setExpanded(True) 
                    else:
                        child=QTreeWidgetItem(parent, [str(sub_key), str(sub_value)])
                        child.setExpanded(True)  
            elif isinstance(value, list):  # Expand list as level 1
                parent = QTreeWidgetItem(self.tree, [str(key), ""])
                parent.setForeground(0, Qt.GlobalColor.magenta)  # Set colour of level 1 key for visibility
                parent.setExpanded(True)  
                for index, item in enumerate(value):  # Level 2
                    child = QTreeWidgetItem(parent, [str(index + 1), str(item)])
                    child.setExpanded(True)  
            else:  # Simple key/value pair
                QTreeWidgetItem(self.tree, [str(key), str(value)])


class GridController(QWidget):
    
    def __init__(self, title=""):
        
        self.COLUMN_MAP = {'Left' : 1, 'Middle' : 2, 'Right' : 3}

        super().__init__()

        layout = QHBoxLayout()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.inspector = InspectorPanel()

        layout.addWidget(self.view)
        layout.addWidget(self.inspector)
        self.setLayout(layout)
        self.setWindowTitle(title)

        #Set up scrollbars - horizontal unlikely to be used
        #self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.view.setStyleSheet("""
            QScrollBar:vertical {
                border: 2px solid #444;
                background: #222;  /* Darker background to stand out */
                width: 18px;  /* Slightly thicker */
                margin: 2px 0px 2px 0px;
            }
            QScrollBar::handle:vertical {
                background: #888; /* Less transparent, more obvious */
                min-height: 30px; /* Larger handle for better visibility */
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                border: none;
            }

            QScrollBar:horizontal {
                border: 2px solid #444;
                background: #222;
                height: 18px;
                margin: 0px 2px 0px 2px;
            }
            QScrollBar::handle:horizontal {
                background: #888;
                min-width: 30px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                border: none;
            }
        """)

        #self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.setGeometry(100, 100, 1600, 300)
        self.setWindowIcon(QIcon(os.path.abspath("json_icon.png")))

        self.maxRow = 5
        self.maxCol = 3

    def populate_cell(self, column, row, width, text_colour, background_colour, label, dictionary):
        if isinstance(column, str):
            column = self.COLUMN_MAP.get(column, 0) # map these strings; otherwise assume they give number {'Left' : 1, 'Middle' : 2, 'Right' : 3}

        cell = GridCell(column, row, width, text_colour, background_colour, label, dictionary, self.inspector.update)
        self.scene.addItem(cell)
        if row>self.maxRow:
            self.maxRow=row
        return cell
    
    def reset_window_height(self):
        theoretical_height = (CELL_HEIGHT + CELL_GAP) * (self.maxRow + 2) #allows for row0 not counting
        #TODO - deal with target_height being greater than screen height

        #current_screen = QApplication.screenAt(self.pos())
        current_screen = self.screen()
        screen_geometry = current_screen.geometry()  
        screen_height = screen_geometry.height()
        print( f"current_screen:'{current_screen.name()}' screen_geometry:{screen_geometry} screen_height:{screen_height}")

        window_geometry = self.geometry()
        current_window_height = window_geometry.height()
        print( f"current_window_height:{current_window_height} theoretical_height:{theoretical_height} self.maxRow:{self.maxRow}")

        #cap target_window_height at screen height.
        target_window_height = min(theoretical_height, screen_height)
        if current_window_height > theoretical_height:
            print( f"leaving window height as-is. current_window_height:{current_window_height} theoretical_height:{theoretical_height} screen_height:{screen_height}")
            return
        
        print( f"target_window_height:{target_window_height} theoretical_height:{theoretical_height} screen_height:{screen_height}")
        window_geometry.setHeight(target_window_height)

        self.setGeometry(window_geometry)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = GridController(title="Demo Workflow")

    task_json = """{
                "Title" : "Boil kettle",
                "Description" : "Click Done when boiled",
                "Steps" : ["Pour the water into the Kettle", "Close lid", "Turn on"],
                "Whatever" : {"a" : "b", "c" : "d", "e" : "f"},
                "DurationSeconds" : 120,
                "Green" : 80,
                "Amber" : 120,
                "Red" : 150,
                "CheckSeverity" : "Low", 
                "CheckMessage" : "Water Boiling?"
            }"""

    task_dict = jsonc.loads(task_json)

    cell=controller.populate_cell(column=1, row=0, width=3, text_colour=Qt.GlobalColor.white, background_colour=Qt.GlobalColor.blue, label="Pre-flight-checks", dictionary=task_dict)
    print("cell.label", cell.label)
    print("cell.CELL_WIDTH", cell.CELL_WIDTH)



    controller.populate_cell(column=1, row=2, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.green, label="Stream1", dictionary={'description': 'more'})
    controller.populate_cell(column=1, row=3, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task1a", dictionary={'description': 'more'})
    controller.populate_cell(column=1, row=4, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task1b", dictionary={'description': 'more'})
    controller.populate_cell(column=1, row=5, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task1c", dictionary={'description': 'more'})
    controller.populate_cell(column=1, row=6, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task1d", dictionary={'description': 'more'})
    controller.populate_cell(column=1, row=7, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Averylongtask", dictionary={'description': 'more'})
    controller.populate_cell(column=1, row=8, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="A very long task", dictionary={'description': 'more'})
    #####
    controller.populate_cell(column=2, row=4, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.black, label="↘️", dictionary={'description': 'Stream2 triggered by Task Task1a '}),
    controller.populate_cell(column=2, row=5, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.green, label="Stream2", dictionary={'description': 'more'}), 

    controller.populate_cell(column=2, row=5, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.green, label="Stream2", dictionary={'description': 'more'})
    controller.populate_cell(column=2, row=6, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task2a", dictionary={'description': 'more'})
    controller.populate_cell(column=2, row=7, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task2b", dictionary={'description': 'more'})
    controller.populate_cell(column=2, row=8, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task2c", dictionary={'description': 'more'})

    controller.populate_cell(column=3, row=7, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.green, label="Stream3", dictionary={'description': 'more'})
    controller.populate_cell(column=3, row=8, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task3a", dictionary={'description': 'more'})
    controller.populate_cell(column=3, row=9, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task3b", dictionary={'description': 'more'})
    controller.populate_cell(column=3, row=10, width=1, text_colour=Qt.GlobalColor.black, background_colour=Qt.GlobalColor.yellow, label="Task3c", dictionary={'description': 'more'})

    controller.populate_cell(column=1, row=32, width=3, text_colour=Qt.GlobalColor.white, background_colour=Qt.GlobalColor.blue, label="Post-flight-checks", dictionary=task_dict)

    controller.reset_window_height() #ensures window fits all columns and rows

    # Use a QTimer to add more cells after 5 seconds without blocking the event loop
    def add_more_cells():
        controller.populate_cell(column=3, row=2, width=1, text_colour=Qt.GlobalColor.white, background_colour=Qt.GlobalColor.red, label="suprise!", dictionary={'description': 'added after delay'})

    QTimer.singleShot(25000, add_more_cells)


    controller.show()

    sys.exit(app.exec())

    ##########

