import sys, os, json, re
import argparse

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QStackedWidget,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QInputDialog

from mimetypes import guess_type


class MediaItem:
    def __init__(self, filepath: str, caption: str):
        self.filepath = filepath
        self.caption = caption
        self.type = self._detect_type()

    def _detect_type(self):
        mimetype, _ = guess_type(self.filepath)
        if mimetype:
            if mimetype.startswith("image"):
                return "image"
            elif mimetype.startswith("video"):
                return "video"
        return None


class MediaList:
    def __init__(self, media_path=None):
        self.items = []
        self.media_path = media_path
        if not self.media_path:
            self.media_path = os.getcwd()

    def load_from_json(self, json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        warnings = []
        for entry in data:
            path = os.path.join(self.media_path, entry.get("filepath"))
            # path = entry.get("filepath")
            caption = entry.get("caption", "")
            if not os.path.exists(path):
                warnings.append(f"File not found: {path}")
                continue
            item = MediaItem(path, caption)
            (
                self.items.append(item)
                if item.type
                else warnings.append(f"Unsupported file type: {path}")
            )
        return warnings


def parse_time_string(s):  # format hh:mm:ss or Xh Ym 3s
    if s is None or s == "" or s.strip() == "":
        raise ValueError("Invalid time format (blank?)")
    s = s.strip()
    s2 = s.replace(" ", "")
    if s2 != s:
        raise ValueError("Invalid time format: no spaces allowed")

    pattern = r"(?:(\d+)\s*h)?(?:(\d+)\s*m)?(?:(\d+)\s*s)?"

    match = re.fullmatch(pattern, s.strip())
    if match:
        hours = int(match.group(1) or 0)  # Default to 0 if None
        minutes = int(match.group(2) or 0)  # Default to 0 if None
        seconds = int(match.group(3) or 0)  # Default to 0 if None
        return hours * 3600 + minutes * 60 + seconds

    if "h" in s or "s" in s or "m" in s:
        if ":" in s:
            raise ValueError("Invalid time format: cannot mix : with h/m/s")

        if not match:
            raise ValueError("Invalid time format (h/m/s) found but not correct")

    else:
        parts = list(map(int, s.strip().split(":")))
        if len(parts) == 1:
            return parts[0]  # Seconds
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]  # Minutes & Seconds
        elif len(parts) == 3:
            return (
                parts[0] * 3600 + parts[1] * 60 + parts[2]
            )  # Hours, Minutes & Seconds
    raise ValueError("Invalid time format")


class SlideShowPlayer(QWidget):
    def __init__(self, media_list: MediaList):
        super().__init__()
        self.media_list = media_list.items
        self.current_index = -1
        self.font_size = 22
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.image_tick_timer = QTimer(self)
        self.image_tick_timer.timeout.connect(self.update_image_time)
        self.remaining_time = 0
        self.elapsed_time = 0
        self.init_ui()
        self.setup_shortcuts()
        self.setWindowTitle("Slideshow Player")
        self.showFullScreen()
        QTimer.singleShot(500, self.next_item)

    def init_ui(self):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background-color: black;")

        self.stack = QStackedWidget()
        self.caption_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.caption_label.setStyleSheet(
            "color: white; font-family: Arial; font-size: 14pt;"
        )
        # buttons
        self.play_button = QPushButton("⏸️")
        self.prev_button = QPushButton("⏮️")
        self.next_button = QPushButton("⏭️")
        self.skip_back_button = QPushButton("⏪")
        self.skip_forward_button = QPushButton("⏩")
        self.jump_button = QPushButton("🦘")
        # tried but didn't look consistent #self.jump_button.setText("⏱️")

        self.jump_button.clicked.connect(self.jump_to_time)

        self.time_remaining_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.time_remaining_label.setStyleSheet("color: white; font-size: 12pt;")

        self.time_elapsed_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.time_elapsed_label.setStyleSheet("color: white; font-size: 12pt;")

        common_button_style = """
QPushButton {
    font-size: 24pt;
    border: none;
    background-color: transparent;
}
QPushButton:pressed {
    background-color: #dddddd;
    border-radius: 8px;
}
QPushButton:disabled {
    background-color: #222222;
    color: #777777;
}
"""

        # apply common_button_style
        for btn in (
            self.prev_button,
            self.skip_back_button,
            self.play_button,
            self.skip_forward_button,
            self.next_button,
            self.jump_button,
        ):
            btn.setStyleSheet(common_button_style)

        self.play_button.clicked.connect(self.toggle_play)
        self.prev_button.clicked.connect(self.prev_item)
        self.next_button.clicked.connect(self.next_item)
        self.skip_back_button.clicked.connect(lambda: self.skip_seconds(-30))
        self.skip_forward_button.clicked.connect(lambda: self.skip_seconds(30))

        btn_layout = QHBoxLayout()
        # Spacer to push buttons to the center
        spacer_left = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        spacer_right = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        btn_layout.addWidget(
            self.time_elapsed_label, alignment=Qt.AlignmentFlag.AlignLeft
        )

        btn_layout.addItem(spacer_left)

        for btn in (
            self.prev_button,
            self.skip_back_button,
            self.play_button,
            self.skip_forward_button,
            self.next_button,
            self.jump_button,
        ):
            btn_layout.addWidget(btn)

        btn_layout.addItem(spacer_right)

        btn_layout.addWidget(
            self.time_remaining_label, alignment=Qt.AlignmentFlag.AlignRight
        )

        layout = QVBoxLayout()

        layout.addWidget(self.stack, stretch=5)
        layout.addWidget(self.caption_label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_max_media_size(self):
        screen_size = QGuiApplication.primaryScreen().availableGeometry().size()
        # Estimate: caption + buttons + margins = approx 150px
        reserved_height = 110
        return screen_size.width(), screen_size.height() - reserved_height

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=self.prev_item)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=self.next_item)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self.toggle_play)

        # QKeySequence("Ctrl++") is really "Ctrl+=" since we don't want to press shift.
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.increase_font)
        QShortcut(QKeySequence("Ctrl+="), self, activated=self.increase_font)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.decrease_font)

        QShortcut(QKeySequence("Ctrl+J"), self, activated=self.jump_to_time)

    def set_button_states_image(self):
        self.prev_button.setToolTip("Go to previous item")
        self.skip_back_button.setToolTip("Go to previous item (on an image)")
        self.play_button.setToolTip("Pause / resume")
        self.skip_forward_button.setToolTip("Go to next item (on an image)")
        self.next_button.setToolTip("Go to next item")
        self.jump_button.setToolTip("Go to next item (on an image)")

    def set_button_states_video(self):
        self.prev_button.setToolTip("Go to previous item")
        self.skip_back_button.setToolTip("Skip back 30 seconds (on a video)")
        self.play_button.setToolTip("Pause / resume")
        self.skip_forward_button.setToolTip("Skip back 30 seconds (on a video)")
        self.next_button.setToolTip("Go to next item")
        self.jump_button.setToolTip("Jump to a point in time (on a video)")

    def clear_current(self):
        self.timer.stop()
        self.image_tick_timer.stop()

        if hasattr(self, "media_player"):
            try:
                self.media_player.mediaStatusChanged.disconnect()
            except TypeError:
                pass
            try:
                self.media_player.positionChanged.disconnect()
            except TypeError:
                pass
            try:
                self.media_player.durationChanged.disconnect()
            except TypeError:
                pass
            self.media_player.stop()
            self.media_player.deleteLater()
            del self.media_player

        if hasattr(self, "audio_output"):
            self.audio_output.deleteLater()
            del self.audio_output

        if hasattr(self, "video_widget"):
            self.stack.removeWidget(self.video_widget)
            self.video_widget.deleteLater()
            del self.video_widget

        if hasattr(self, "image_label"):
            self.stack.removeWidget(self.image_label)
            self.image_label.deleteLater()
            del self.image_label

    @property  # can be called as self.current_item
    def current_item(self):
        return self.media_list[self.current_index]

    def display_item(self):
        self.clear_current()
        item = self.current_item  # self.media_list[self.current_index]
        self.caption_label.setText(item.caption)
        self.caption_label.setStyleSheet(
            f"color: white; font-family: Arial; font-size: {self.font_size}pt;"
        )

        if item.type == "image":
            self.image_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(item.filepath)
            max_width, max_height = self.get_max_media_size()
            scaled = pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.image_label.setMaximumSize(max_width, max_height)
            self.stack.addWidget(self.image_label)
            self.stack.setCurrentWidget(self.image_label)
            self.start_timer(7000)
            self.set_button_states_image()

        elif item.type == "video":
            self.video_widget = QVideoWidget()
            max_width, max_height = self.get_max_media_size()
            self.video_widget.setMaximumSize(max_width, max_height)
            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setVideoOutput(self.video_widget)
            self.media_player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(1.0)

            self.stack.addWidget(self.video_widget)
            self.stack.setCurrentWidget(self.video_widget)

            self.media_player.setSource(QUrl.fromLocalFile(item.filepath))
            self.media_player.play()
            self.media_player.mediaStatusChanged.connect(self.check_video_end)
            self.media_player.positionChanged.connect(self.update_time_label)
            self.media_player.durationChanged.connect(self.update_time_label)
            self.set_button_states_video()

    def start_timer(self, ms):
        self.remaining_time = ms
        self.elapsed_time = 0
        self.update_time_label()
        self.image_tick_timer.start(1000)
        self.timer.timeout.connect(self.next_item)
        self.timer.start(ms)

    def format_time(self, ms, postscript=""):
        if True:
            seconds = ms // 1000
            if seconds < 60:
                return f"{seconds}s {postscript}"
            elif seconds < 3600:
                minutes = seconds // 60
                secs = seconds % 60
                return f"{minutes}:{secs:02d} {postscript}"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                return f"{hours}:{minutes:02d}:{secs:02d} {postscript}"

    def update_time_label(self):
        if hasattr(self, "media_player"):
            duration = self.media_player.duration()
            pos = self.media_player.position()
            if duration > 0:
                remaining = max(0, duration - pos)
                self.time_remaining_label.setText(self.format_time(remaining))
                self.time_elapsed_label.setText(self.format_time(pos))
            else:
                self.time_remaining_label.setText("")
                self.time_elapsed_label.setText("")
            return

        if hasattr(self, "remaining_time"):
            self.time_remaining_label.setText(
                self.format_time(self.remaining_time, "left")
            )
        if hasattr(self, "elapsed_time"):
            self.time_elapsed_label.setText(self.format_time(self.elapsed_time))

    def update_image_time(self):
        if self.remaining_time > 1000:
            self.remaining_time -= 1000
        else:
            self.remaining_time = 0
        self.elapsed_time += 1000
        self.update_time_label()

    def check_video_end(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            QTimer.singleShot(500, self.next_item)

    def next_item(self):
        self.current_index = (self.current_index + 1) % len(self.media_list)
        self.display_item()

    def prev_item(self):
        self.current_index = (self.current_index - 1) % len(self.media_list)
        self.display_item()

    def toggle_play(self):
        if self.current_item.type == "video" and hasattr(self, "media_player"):
            if (
                self.media_player.playbackState()
                == QMediaPlayer.PlaybackState.PlayingState
            ):
                self.media_player.pause()
                self.play_button.setText("▶️")
            else:
                self.media_player.play()
                self.play_button.setText("⏸️")
            return
        if self.current_item.type == "image":
            if self.timer.isActive():  # time is ticking down on the image...
                self.timer.stop()
                self.image_tick_timer.stop()
                self.play_button.setText("▶️")
            else:
                self.timer.start()
                self.image_tick_timer.start()
                self.play_button.setText("⏸️")

    def skip_seconds(self, seconds):
        if hasattr(self, "media_player"):
            new_pos = max(0, self.media_player.position() + seconds * 1000)
            self.media_player.setPosition(new_pos)
        else:
            if seconds < 0:
                self.prev_item()
            else:
                self.next_item()

    def jump_to_time(self):
        if self.current_item.type == "image":
            self.next_item()
            return

        time_str, ok = QInputDialog.getText(
            self, "Jump to Time", "Enter time (hh:mm:ss, mm:ss, or ss):"
        )
        if not ok or not time_str.strip():
            return

        try:
            total_seconds = parse_time_string(time_str)
            target_ms = total_seconds * 1000
            duration = self.media_player.duration()
            if duration > 0:
                if target_ms >= duration:
                    target_ms = max(0, duration - 1000)
                self.media_player.setPosition(target_ms)
                print(f"Jumped to {target_ms} ms")
            else:
                QMessageBox.warning(self, "Jump Failed", "Media not fully loaded yet.")
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Format", "Could not parse the time format."
            )

    def increase_font(self):
        self.font_size = min(30, self.font_size + 2)
        self.caption_label.setStyleSheet(
            f"color: white; font-family: Arial; font-size: {self.font_size}pt;"
        )

    def decrease_font(self):
        self.font_size = max(6, self.font_size - 2)
        self.caption_label.setStyleSheet(
            f"color: white; font-family: Arial; font-size: {self.font_size}pt;"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Player of slideshows to help with recipes"
    )
    parser.add_argument(
        "--file",
        required=False,
        help="Path to the JSON file containing the slideshow definition",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path to the media files",
    )

    return parser.parse_args()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    args = parse_args()
    if args.file:
        file = args.file
    else:
        file, _ = QFileDialog.getOpenFileName(
            None, "Select JSON file", "", "JSON Files (*.json)"
        )
    if not file or not os.path.exists(file):
        print("Unable to process without valid file")
        sys.exit()
    if args.path:
        if not os.path.exists(args.path):
            print(f"Invalid path {args.path}")
            sys.exit()

    media_path = args.path
    media_list = MediaList(media_path)
    warnings = media_list.load_from_json(file)

    if warnings:
        QMessageBox.warning(None, "Media Load Warnings", "\n".join(warnings))

    if not media_list.items:
        QMessageBox.critical(None, "No Valid Media", "No valid media items found.")
        sys.exit()

    player = SlideShowPlayer(media_list)
    sys.exit(app.exec())
