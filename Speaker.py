"""
The idea now is that the Main UI application will create a thread for the player, and then tasks will call the player.
Potentially link the player to the Main UI to populate a status bar.
------
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
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication


class Speaker(QObject):
    #thread safe signal mechanisms - in final app this would allow different instances of Task to interact AudioWorker

    def __init__(self, temp_folder):
        super().__init__()
        self.temp_folder = temp_folder

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(1)



    def stop(self):
        self.player.stop()

    def play(self, path: str):
        self.stop()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def speak(self, text: str):
        filename = "".join(c for c in text if c.isalnum() or c == "_") + ".mp3"
        path = os.path.join(self.temp_folder, filename)

        if not os.path.exists(path):
            print(f"[AudioWorker] Generating speech for '{text}'...")
            tts = gTTS(text=text, lang='en', tld='ie')  # Irish English
            tts.save(path)

        self.play(path)

    def play_audio_file(self, filename: str):
        path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(path):
            self.play(path)
        else:
            print(f"File not found: {path}")

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_folder)
            print(f"Speaker:Temp folder deleted: {self.temp_folder}")
        except Exception as e:
            print(f"Speaker:Failed to delete temp folder: {e}")
    def fun_alert(self):
        self.play_audio_file("resources\audio/submarine.mp3")
    def fun_alert2(self):
        self.play_audio_file("resources\audio/ping.mp3")





if __name__ == "__main__":
    sys.exit(0)
