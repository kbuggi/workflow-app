import sys
import pyttsx3
import logging

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar, QDialog, QComboBox, QLabel, QPushButton, QSpinBox, QFontComboBox, QTabWidget, QRadioButton, QGroupBox, QVBoxLayout
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction, QFont


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 400, 350)

        self.settings = QSettings("KatalinaM", "Timer")

        # UI Elements
        self.layout = QVBoxLayout()

        # Create Tab Widget
        self.tab_widget = QTabWidget(self)

        # Font Settings Tab
        self.font_tab = QWidget()
        self.font_layout = QVBoxLayout()

        # Font Selection
        self.font_label = QLabel("Select Font Family:")
        self.font_combo = QFontComboBox()
        font_family = self.settings.value("font_family", "Arial")
        self.font_combo.setCurrentFont(QFont(font_family))  # Convert font name to QFont object
        
        # Font Size Selection
        self.font_size_label = QLabel("Select Font Size:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 30)
        self.font_size_spinbox.setValue(self.settings.value("font_size", 12))

        # Sample text for font preview
        self.sample_text_label = QLabel("Sample Text: 'The quick brown fox jumps over the lazy dog'")
        self.sample_text_label.setFont(QFont(font_family, self.settings.value("font_size", 12)))

        # Connect signals
        self.font_size_spinbox.valueChanged.connect(self.update_sample_text_font_size)
        self.font_combo.currentFontChanged.connect(self.update_sample_text_font_family)

        self.font_layout.addWidget(self.font_label)
        self.font_layout.addWidget(self.font_combo)
        self.font_layout.addWidget(self.font_size_label)
        self.font_layout.addWidget(self.font_size_spinbox)
        self.font_layout.addWidget(self.sample_text_label)

        self.font_tab.setLayout(self.font_layout)

        # Voice Settings Tab
        self.voice_tab = QWidget()
        self.voice_layout = QVBoxLayout()

        # Voice Selection
        self.voice_label = QLabel("Select Voice:")
        self.voice_dropdown = QComboBox()

        # Voice Filters (Gender and Language)
        self.filter_label = QLabel("Filter by dialect:")
        self.filter_dropdown = QComboBox()
        self.gender_label = QLabel("Filter by gender:")
        self.gender_dropdown = QComboBox()

        self.play_button = QPushButton("Play Sample")
        self.save_button = QPushButton("Save Preferences")
        self.done_button = QPushButton("Done")  # New Done button

        self.engine = pyttsx3.init()
        self.voices = self.get_english_voices()  # Load all English voices
        self.filtered_voices = self.voices

        # Populate dropdowns
        self.populate_voice_dropdown(self.filtered_voices)
        self.filter_dropdown.addItems(["All"] + sorted(set(v["lang"] for v in self.voices)))
        
        # Dynamically populate gender filter based on actual genders present in voices
        gender_set = set(v["gender"] for v in self.voices if v["gender"] is not None)
        self.gender_dropdown.addItems(["All"] + sorted(gender_set))

        # Load last saved voice
        last_voice = self.settings.value("selected_voice", "")
        if last_voice:
            index = next((i for i, v in enumerate(self.filtered_voices) if v["id"] == last_voice), 0)
            self.voice_dropdown.setCurrentIndex(index)

        # Layout Setup
        self.voice_layout.addWidget(self.voice_label)
        self.voice_layout.addWidget(self.voice_dropdown)
        self.voice_layout.addWidget(self.filter_label)
        self.voice_layout.addWidget(self.filter_dropdown)
        self.voice_layout.addWidget(self.gender_label)
        self.voice_layout.addWidget(self.gender_dropdown)
        self.voice_layout.addWidget(self.play_button)
        self.voice_layout.addWidget(self.save_button)
        self.voice_layout.addWidget(self.done_button)  # Add Done button
        self.voice_tab.setLayout(self.voice_layout)

        # Add tabs to the tab widget
        self.tab_widget.addTab(self.font_tab, "Font Settings")
        self.tab_widget.addTab(self.voice_tab, "Voice Settings")

        # Save and Cancel Buttons
        self.save_button.clicked.connect(self.save_preference)
        self.done_button.clicked.connect(self.accept)  # Done button closes the window

        # Signals
        self.play_button.clicked.connect(self.play_sample)
        self.filter_dropdown.currentTextChanged.connect(self.filter_voices)
        self.gender_dropdown.currentTextChanged.connect(self.filter_voices)

        # Final Layout
        self.layout.addWidget(self.tab_widget)

    def fontsize_value_changed(self, value=0):
        logger.debug("Font Value Changed()")
        if value > 0:
            font_size = value 
        else:
            font_size = self.font_size_spinbox.value()
        font_family = self.font_combo.currentFont().family()
        self.sample_text_label.setFont(QFont(font_family, font_size))

    def update_sample_text_font_family(self, font):
        font_size = self.font_size_spinbox.value()  # Get the current font size from the spinbox
        self.sample_text_label.setFont(QFont(font.family(), font_size))  # Update the font family and size

    # Method to update the font size of the sample text label
    def update_sample_text_font_size(self, value):
        font_family = self.font_combo.currentFont().family()  # Get the current font family
        self.sample_text_label.setFont(QFont(font_family, value))  # Update the font size

    def update_sample_text_font_family(self, value):
        font_family = self.font_combo.currentFont().family()  # Get the current font family
        font_size=self.font_size_spinbox.value()
        self.sample_text_label.setFont(QFont(font_family, font_size))  # Update the font size
     

    def get_english_voices(self):
        """Retrieve all English voices available on the system."""
        voices = []
        for voice in self.engine.getProperty("voices"):
            lang = voice.languages[0] if isinstance(voice.languages, list) else voice.languages
            if lang.startswith("en"):  # Only English voices
                voices.append({"id": voice.id, "name": voice.name, "lang": lang, "gender": voice.gender})
        return voices

    def populate_voice_dropdown(self, voices):
        """Populate voice dropdown with available voices."""
        self.voice_dropdown.clear()
        self.voice_dropdown.addItems([v["name"] for v in voices])

    def filter_voices(self):
        """Filter voices based on language and gender."""
        language_filter = self.filter_dropdown.currentText()
        gender_filter = self.gender_dropdown.currentText()

        # Apply language filter
        if language_filter != "All":
            self.filtered_voices = [v for v in self.voices if language_filter in v["lang"]]
        else:
            self.filtered_voices = self.voices

        # Apply gender filter
        if gender_filter != "All":
            self.filtered_voices = [v for v in self.filtered_voices if gender_filter == v["gender"]]

        # Populate the voice dropdown with filtered voices
        self.populate_voice_dropdown(self.filtered_voices)

    def play_sample(self):
        """Play a sample phrase using the selected voice."""
        selected_index = self.voice_dropdown.currentIndex()
        selected_voice = self.filtered_voices[selected_index]
        selected_voice_id = selected_voice["id"]
        print(f"Sampling voice: {selected_voice['name']} (ID: {selected_voice_id})")
        self.engine.setProperty("voice", selected_voice_id)
        self.engine.say("The cat sat on the mat.")
        self.engine.runAndWait()

    def save_preference(self):
        font_family = self.font_combo.currentFont().family()
        font_size = self.font_size_spinbox.value()
        selected_voice = self.filtered_voices[self.voice_dropdown.currentIndex()]["id"]
        print(f"Save font family {font_family}, font size {font_size}, and selected voice {selected_voice} to QSettings.")

        self.settings.setValue("font_family", font_family)
        self.settings.setValue("font_size", font_size)
        self.settings.setValue("selected_voice", selected_voice)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")

        # Load settings
        self.settings = QSettings("Katalina", "AppSettings")
        self.font_family = self.settings.value("font_family", "Arial")
        self.font_size = self.settings.value("font_size", 12)
        self.selected_voice = self.settings.value("selected_voice", "")

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.settings_menu = self.menu_bar.addMenu("Settings")
        self.settings_action = QAction("Settings...", self)
        self.settings_menu.addAction(self.settings_action)
        self.settings_action.triggered.connect(self.open_settings)

        # Main Window Layout
        self.layout = QVBoxLayout()
        self.label = QLabel("Sample text")
        self.label.setFont(QFont(self.font_family, self.font_size))  # Update the font size
        self.layout.addWidget(self.label)

        self.button = QPushButton("Settings...")
        self.button.setStyleSheet(f"font-family: {self.font_family}; font-size: {self.font_size}px;")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.open_settings)  


        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def open_settings(self):
        """Open the settings dialog."""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec() == QDialog.accepted:
            # Update the main window with new settings
            print("Settings saved")
        self.font_family = self.settings.value("font_family", "Arial")
        self.font_size = self.settings.value("font_size", 12)
        self.selected_voice = self.settings.value("selected_voice", "")

        # Debugging: Print the updated values
        print(f"Updated font_family: {self.font_family}")
        print(f"Updated font_size: {self.font_size}")
        self.label.setFont(QFont(self.font_family, self.font_size))  # Update the font size



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
