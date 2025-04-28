"""
This demonstration code is a simple PyQt6 application that plays audio files and uses gTTS (Google Text-to-Speech) to generate speech from text. 
gTTS means internet access is required to generate the speech.
- therefore we cache the generated speech in a temporary folder
- and delete it when the app closes.
- The application uses QMediaPlayer and QAudioOutput from PyQt6 to handle audio playback.
Experimented with threading to ensure that the UI remains responsive while audio is being played or speech is being generated.
- The UI (MainWindow) creates a thread for the player using QThread
- The AudioWorker class handles audio playback and speech generation in that created thread.
- The UI (MainWindow) triggers audio/speech playback by sending thread-safe signals to the AudioWorker.
- The AudioWorker uses signals to communicate back to the UI about the status of playback and speech generation to update the statusbar.
"""

import sys
import os
import tempfile
import shutil
from gtts import gTTS
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QVBoxLayout, QStatusBar, QLabel
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, QObject
from PyQt6.QtMultimedia import QMediaPlayer

from Speaker import Speaker




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test")

        # Create a dedicated temporary folder
        self.temp_subfolder = tempfile.mkdtemp(prefix="audio_tts_")

        # Set up central widget and layout
        central = QWidget()
        layout = QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)


        # Buttons
        self.audio_button1 = QPushButton("Play Audio 1")
        self.audio_button2 = QPushButton("Play Audio 2")
        self.tts_button1 = QPushButton("Speak: Hello World")
        self.tts_button2 = QPushButton("Speak: Happy Viva")

        layout.addWidget(self.audio_button1)
        layout.addWidget(self.audio_button2)
        layout.addWidget(self.tts_button1)
        layout.addWidget(self.tts_button2)

        # Set up audio worker in a thread
        self.thread = QThread()
        self.worker = Speaker(self.temp_subfolder)
        self.worker.moveToThread(self.thread)
        self.thread.start()


        # Connect buttons
        self.audio_button1.clicked.connect(lambda: self.worker.play_audio_file("resources\audio/ping.mp3"))
        self.audio_button2.clicked.connect(lambda: self.worker.play_audio_file("resources\audio/submarine.mp3"))
        self.tts_button1.clicked.connect(lambda: self.worker.speak("Hello world"))
        self.tts_button2.clicked.connect(lambda: self.worker.speak("Happy Viva"))

    def closeEvent(self, event):
        self.worker.stop()
        self.worker.cleanup()
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
