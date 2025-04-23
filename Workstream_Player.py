import sys, platform
from PyQt6.QtCore import QTimer, Qt, QSettings
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QMenuBar, QWidget, QLabel, QVBoxLayout, QPushButton, QFrame, QTextEdit, QHBoxLayout, QStatusBar
from PyQt6.QtGui import QFont, QTextFormat, QTextBlockFormat, QTextCursor, QFontMetrics, QFontDatabase
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, QObject


import time
import logging
import jsonc, json
import sys
import typing
import tempfile

import argparse

#allows workaround for macOS/Qt limitation
try:
    from AppKit import NSApplication, NSApp
except ImportError:
    NSApplication = None 

from Speaker import Speaker

from WorkflowStream import WorkflowStream, Checklist, Stream, Task, Live, Helper

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


#TODO - implement a CountUp timer. Basically the same in terms of display; just calculation & comparison is different
#TODO - rename - arguably this should be called something like StreamExecution
class CountdownTimer(QWidget):
    BG_COLOUR = "DarkGrey"
    ACTIVE_BG_COLOUR = "White"

    """ 
        using shared register of streams to make sure we don't get cyclic behaviour
        research shows an alterate approach using weakref.WeakValueDictionary - no need
        likewise could explicitly remove stream from register when user closes/deletes it - no need
    """
    _instances = {}  # Shared registry of instances; ensure cyclic behaviour cannot occur

    def __new__(cls, stream : Stream, *args, **kwargs):
        name = str(stream.name)
        if name.lower().endswith("checklist"):
            logger.warning(f"__new__ in CountdownTimer invoked on a checklist {name}")
        else:
            logger.info(f"__new__ in CountdownTimer invoked on a non-checklist {name}")
            if stream.name in cls._instances:
                logger.exception("Stream {stream.name} triggered; already running/in register")
                raise ValueError(f"An instance with stream_name '{stream.name}' has already been triggered/in register!")

        instance = super().__new__(cls)
        cls._instances[stream.name] = instance  # Store the new instance
        return instance


    def __init__(self, stream: Stream, parent_layout: QHBoxLayout, auto_start : bool, parent_instance ): 
        super().__init__()   #-> QWidget

        self.speaker = parent_instance.speaker
        self.parent_instance = parent_instance 
        self._parent_layout = parent_layout #parent_layout to be able add a stream triggered by a task in this stream
        self.stream = stream
        self.current_task = stream.task_first
        self.init_UI()
        self.reset_state_jumped_task()
        self.tick = app.settings.value("local_tick")
        if auto_start:     # Timer is started automatically if the stream is triggered by another stream/task
            self.start_timer() 
        else:
            self.timer_running = False  # User has to start the timer on first task in GO stream
        self.reset_UI()
        self.triggered_Instances=[]
        self.triggered_names=[]



    def reset_state_jumped_task(self):
        #resume state if it has been started before
        if "live" in self.current_task.__dict__:
            self.live = self.current_task.live
            #User feedback change -  we "floor" the timer at 30 seconds if the user goes back
            if self.live.remaining_time < 30 and self.current_task.duration > 30:
                self.live.remaining_time = 30
        else:
            self.current_task.live = Live()
            self.live = self.current_task.live
            self.live.bg_colour = self.BG_COLOUR
            self.live.duration = self.current_task.duration  
            self.live.remaining_time = self.live.duration  # Initialize remaining time with the total time
            self.live.extend_count = 0  # Initialize extend count
            self.live.reduce_count = 0  # Initialize count
            self.live.pause_count = 0  # Initialize count
            self.live.red = self.current_task.red
            self.live.amber = self.current_task.amber
            self.live.green = self.current_task.green
            #User feedback change - changed format of title box text - stream title
            self.live.title_text = f"Stream: {self.stream.title}"
            #User feedback change - put the task name in the second box instead of description
            self.live.description_text = self.current_task.title
            if self.current_task.description is not None and self.current_task.description != "":
                self.live.steps_text = self.current_task.description + "\n\n" 
            else:
                self.live.steps_text = ""
            self.live.steps_text += "\n".join(f"• {step}" for step in self.current_task.steps) # Bullet list 
            #User feedback change - put the description into the task box
        if self.current_task.StartMessage != "":
            logger.info(f"{self.current_task.title}:  Starting task; generating alert: {self.current_task.StartMessage}")
            self.speaker.speak(self.current_task.StartMessage)
            self.status_label.setText(f"**** {self.current_task.StartMessage} *****")
    

    def reset_UI(self):
        self.title_label.setText(self.live.title_text)
        self.description_label.setText(self.live.description_text)
        self.steps_label.setPlainText(self.live.steps_text)  
        self.update_status_label()
        self.update_timer_display()  # Initialize the label with the formatted time
        self.update_button_states()
        self.update_background_colour()
        if self.current_task.StartMessage != "":
            logger.info(f"{self.current_task.title}:  Starting task; generating alert: {self.current_task.StartMessage}")
            self.speaker.speak(self.current_task.StartMessage)
            self.status_label.setText(f"**** {self.current_task.StartMessage} *****")
    
    def update_bg_colour_widget(self,widget : QWidget, old_col : str, new_col : str):
        old_style = widget.styleSheet()
        new_style = old_style.replace(old_col, new_col)
        widget.setStyleSheet(new_style)

    def update_background_colour(self):
        #User feedback change -  we make active tasks clearer from background tasks via distinct background colours
        if self.current_task.type == "Active":
            bg_colour = self.ACTIVE_BG_COLOUR
            old_bg_colour = self.BG_COLOUR
            logger.info("SETTING TASK ACTIVE")  
        else:
            bg_colour = self.BG_COLOUR
            old_bg_colour = self.ACTIVE_BG_COLOUR

        self.update_bg_colour_widget(self.text_box_frame, old_bg_colour, bg_colour)
        #No need to iterate through child widgets; they seem to update automatically

    def init_UI(self):
        self.setWindowTitle("Countdown Timer")
        self.setGeometry(100, 100, 1200, 800) #X, Y, WIDTH, HEIGHT

        # Layout
        self.layout = QVBoxLayout()

        # Create a QFrame (box) for both the title and description
        self.text_box_frame = QFrame(self)
        self.text_box_frame.setStyleSheet(f"border: 2px solid black; border-radius: 10px; padding: 10px; background-color: {self.BG_COLOUR};")
        self.layout.addWidget(self.text_box_frame)

        # Layout for the text box (title + description)
        text_box_layout = QVBoxLayout()

        # Title label inside the box
        self.title_label = QLabel(self.text_box_frame)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set a larger font for the title
        title_font = QFont("Arial", 16) 
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: black;")  
        text_box_layout.addWidget(self.title_label)

        # Description label inside the box (single-line)
        self.description_label = QLabel(self.text_box_frame)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description_font = QFont("Arial", 18)
        self.description_label.setFont(description_font)
        self.description_label.setStyleSheet("color: black; font-style: italic;")

        text_box_layout.addWidget(self.description_label)

        # Steps label inside the box (multi-line)
        self.steps_label = QTextEdit(self.text_box_frame)
        self.steps_label.setReadOnly(True)  

        steps_font = QFont( app.settings.value("fixed_font"), 18)
        self.steps_label.setFont(steps_font)
        # Get the text cursor for the QTextEdit
        cursor = self.steps_label.textCursor()

        # Select the entire document
        cursor.select(QTextCursor.SelectionType.Document)

        # Create a QTextBlockFormat and set the line height
        block_format = QTextBlockFormat()
        block_format.setLineHeight(150, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)  # 150% line height

        # Apply the block format to the selected text
        cursor.mergeBlockFormat(block_format)
        self.steps_label.setTextCursor(cursor)
        self.steps_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steps_label.setStyleSheet("color: black; ")
        font_metrics = QFontMetrics(self.steps_label.font())
        line_height = font_metrics.lineSpacing() 
        #self.steps_label.setMinimumHeight( int(10 * 18 * 1.5))  #roughly 10 rows but hardcoding of fontsize
        self.steps_label.setMinimumHeight( int(10 * line_height) + 22 ) #padding & border radius  

        text_box_layout.addWidget(self.steps_label)

        self.setLayout(self.layout)


        # Set the layout for the text box
        self.text_box_frame.setLayout(text_box_layout)

        # Create Timer 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        # Create a QFrame (box) for the timer
        self.timer_box = QFrame(self)
        self.timer_box.setStyleSheet("border: 2px solid black; border-radius: 10px; padding: 10px; background-color: lightgrey;")
        self.layout.addWidget(self.timer_box)

        # Timer display label inside the box
        self.timer_label = QLabel(self.timer_box)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set a larger font for the timer display
        font = QFont("Arial", 30)
        self.timer_label.setFont(font)
        self.timer_label.setStyleSheet("color: black;")  

        # Add the label to the timer box layout
        box_layout = QVBoxLayout()
        box_layout.addWidget(self.timer_label)
        self.timer_box.setLayout(box_layout)

        # Status label; this sits on a black background hence white font. Blank at start
        self.status_label = QLabel(self) 
        self.status_label.setText(f"") 
        self.status_label.setStyleSheet("color: white;")  
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Buttons: Start, Done, Snooze, and Delete; only Done is active
        #User feedback change -  icons not words or words & icons
        #switch the order

        #Pause/Start & layout
        self.pause_button = QPushButton("⏸️", self)
        self.pause_button.setStyleSheet("color: black;")  
        self.pause_button.clicked.connect(self.pressed_pause)
        self.pause_button.setEnabled(False)

        self.resume_button = QPushButton("▶️", self)
        self.resume_button.setStyleSheet("color: black;")  
        self.resume_button.clicked.connect(self.pressed_resume)
        self.resume_button.setEnabled(False)

        self.resume_pause_button_layout = QHBoxLayout()
        self.resume_pause_button_layout.addWidget(self.pause_button)
        self.resume_pause_button_layout.addWidget(self.resume_button)
        self.layout.addLayout(self.resume_pause_button_layout)


        #Extend/Reduce & layout
        self.reduce_button = QPushButton("➖ 30s", self)
        self.reduce_button.setStyleSheet("color: black;")  
        self.reduce_button.clicked.connect(self.pressed_reduce)
        self.reduce_button.setEnabled(False)

        self.extend_button = QPushButton("➕ 30s", self)
        self.extend_button.setStyleSheet("color: black;")  
        self.extend_button.clicked.connect(self.pressed_extend)
        self.extend_button.setEnabled(False)

        self.reduce_extend_button_layout = QHBoxLayout()
        self.reduce_extend_button_layout.addWidget(self.reduce_button)
        self.reduce_extend_button_layout.addWidget(self.extend_button)
        self.layout.addLayout(self.reduce_extend_button_layout)

        #Done button; initially labelled "Start"
        self.done_button = QPushButton("⏭️ Start", self)
        done_font = QFont("Arial", 20)
        self.done_button.setFont(done_font)
        self.done_button.setStyleSheet("color: black;")  
        self.done_button.clicked.connect(self.pressed_done_next_task)
        self.done_button.setEnabled(True)

        self.done_button_layout = QHBoxLayout()
        self.done_button_layout.addWidget(self.done_button)
        self.layout.addLayout(self.done_button_layout)




        # Back/Close & layout
        self.back_button = QPushButton("(⏮️ back)", self)
        self.back_button.setStyleSheet("color: black;")  
        self.back_button.clicked.connect(self.pressed_back)
        self.back_button.setEnabled(False)

        self.delete_button = QPushButton("🗑️", self)
        self.delete_button.setStyleSheet("color: black;")  
        self.delete_button.clicked.connect(self.pressed_close_stream)
        self.delete_button.setEnabled(False)

        self.back_close_button_layout = QHBoxLayout()
        self.back_close_button_layout.addWidget(self.back_button)
        self.back_close_button_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.back_close_button_layout)


        # Tweak spacing - Main layout
        self.layout.setSpacing(5)  # Reduce spacing between widgets
        self.layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins around the layout

        # Done button layout
        self.done_button_layout.setSpacing(5)
        self.done_button_layout.setContentsMargins(0, 0, 0, 0)

        # Start/Pause button layout
        self.resume_pause_button_layout.setSpacing(5)
        self.resume_pause_button_layout.setContentsMargins(0, 0, 0, 0)

        # Reduce/Extend button layout
        self.reduce_extend_button_layout.setSpacing(5)
        self.reduce_extend_button_layout.setContentsMargins(0, 0, 0, 0)

        # Back/Close button layout
        self.back_close_button_layout.setSpacing(5)
        self.back_close_button_layout.setContentsMargins(0, 0, 0, 0)

        #User feedback change -  add tool tips to explain buttons
        # Tooltips for buttons
        self.done_button.setToolTip("Press when task is done to move to next task in stream")
        self.resume_button.setToolTip("Resume timer after pausing")
        self.pause_button.setToolTip("Pause timer - don't forget to resume it")
      
        self.back_button.setToolTip("Go back to previous task")
        self.delete_button.setToolTip("Delete this Stream (can only be pressed once all tasks in this Stream are done)")

        self.extend_button.setToolTip("Add 30 seconds to timer")
        self.reduce_button.setToolTip("Remove 30 seconds from timer")

        # Initial state
        self.setLayout(self.layout)

    def overrun_alert(self):
        logger.info(f"{self.current_task.title}:  Timer overrun; generating alert: {self.current_task.CheckMessage}")
        self.status_label.setText(f"**** {self.current_task.CheckMessage} *****")
        self.speaker.speak(self.current_task.CheckMessage)

    #User feedback change -  ensure there is a message for all overrunning tasks
    def overrun_alert_no_msg(self):
        msg = f"Overrun {self.stream.title}"
        logger.info(f"Overrun on task with no specific message:{msg}")
        self.status_label.setText(f"**** {msg} *****")
        self.speaker.speak(msg)




    def update_timer(self):
        self.live.remaining_time -= self.tick # Decrease the timer by tick seconds
        if self.current_task.Autoprogress:
            # Check if the timer has reached zero
            if self.live.remaining_time <= 0:
                logger.info(f"{self.current_task.title}:  Timer expired; moving to next task")
                self.speaker.fun_alert2()
                self.pressed_done_next_task()
                return

        if self.live.remaining_time == 0 and self.current_task.CheckEverySeconds > 0:
            self.overrun_alert()
        elif self.live.remaining_time < 0 and self.current_task.CheckEverySeconds > 0 and self.live.remaining_time % self.current_task.CheckEverySeconds == 0:
            self.overrun_alert()
        elif self.live.remaining_time == 0:
            self.overrun_alert_no_msg()

        # Update the timer label text
        self.update_timer_display()

        # Change background color based on remaining time
        self.update_timer_colour()



    def update_timer_display(self, force_update : bool = False):
        #User feedback change -  show 5 second updates 
        # 10 -> 10; 9->10; 6 -> 10; 5 -> 5; 4 -> 5
        # Unless user just pressed extend/reduce
        if not force_update and self.live.remaining_time % 5 != 0:
            return #leave clock as is
        # from background tasks via distinct background colours
        if self.live.remaining_time >= 60:
            # Show minutes and seconds in mm:ss format
            minutes = self.live.remaining_time // 60
            seconds = self.live.remaining_time % 60
            self.timer_label.setText(f"{minutes:02}:{seconds:02}")            
        elif self.live.remaining_time <= -60:
            # Show minutes and seconds in -mm:ss format
            minutes = (0 - self.live.remaining_time) // 60
            seconds = (0 - self.live.remaining_time) % 60

            #User feedback change -  "overrun" not "-" 
            self.timer_label.setText(f"overrun {abs(minutes):02}:{seconds:02}")
        elif self.live.remaining_time <= 0:
            seconds = abs(self.live.remaining_time)
            #User feedback change -  "overrun 0s" not "-0s" 
            self.timer_label.setText(f"overrun {seconds}s")
        else:
            # Show seconds only
            self.timer_label.setText(f"{self.live.remaining_time}s")

    def update_timer_colour(self, grey : bool = False): 
        #background of clock grey->green->amber->red --> grey when all tasks are done; stays that colour when snoozed

        if self.live.remaining_time <= self.live.red: 
            self.timer_box.setStyleSheet("border: 2px solid black; background-color: red; border-radius: 10px; padding: 10px;")
        elif self.live.remaining_time <= self.live.amber:
            self.timer_box.setStyleSheet("border: 2px solid black; background-color: yellow; border-radius: 10px; padding: 10px;")
        elif self.live.remaining_time <= self.live.green: 
            self.timer_box.setStyleSheet("border: 2px solid black; background-color: lightgreen; border-radius: 10px; padding: 10px;")
        elif self.current_task.type == "Active": 
            self.timer_box.setStyleSheet(f"border: 2px solid black; background-color: {self.ACTIVE_BG_COLOUR}; border-radius: 10px; padding: 10px;")
        else: #GREY
            self.timer_box.setStyleSheet(f"border: 2px solid black; background-color: {self.BG_COLOUR}; border-radius: 10px; padding: 10px;")

    def update_button_states(self):
        """Update the state of buttons based on the timer's running state."""
        if self.timer_running:
            # When the timer is running, disable the resume button and enable pause/snooze
            self.resume_button.setDisabled(True)
            self.pause_button.setEnabled(True)
            self.extend_button.setEnabled(True)
            self.reduce_button.setEnabled(True)
            self.done_button.setEnabled(True)
        else:
            # When the timer is not running, enable the resume/resume button (done can be pressed anyway)
            self.resume_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.extend_button.setEnabled(False)
            self.reduce_button.setEnabled(False)

        if self.current_task.task_previous is None:
            self.back_button.setDisabled(True) 
        else:
            self.back_button.setEnabled(True) 


        # Allow delete only at the end of the Stream when done has been pressed 
        if self.current_task.task_next is None:
            if  self.timer_running:  #entering final task
                logger.info("Final task; OK to press Done")
                self.done_button.setText("⏭️ Done [Final Task]")
            else: #final task is now done
                logger.info("Enabling delete button/Disabling all other buttons")
                self.done_button.setText("[No tasks remaining]")
                self.delete_button.setEnabled(True)
                self.done_button.setDisabled(True)
                self.pause_button.setDisabled(True)
                self.resume_button.setDisabled(True) 
                self.extend_button.setDisabled(True)
                self.reduce_button.setDisabled(True)
                self.update_button_colors()
                #User feedback change -  play happy sound on last task
                self.parent_instance.speaker.fun_alert()
                #User feedback change -  open checklist automatically on last task
                self.parent_instance.open_post_checklist()
        else:
            self.delete_button.setDisabled(True)
            if self.timer_running:
                self.done_button.setText("⏭️ Done")


        # Update button colors for visual feedback
        self.update_button_colors()

    def update_button_colors(self): #TODO maybe have a list of buttons & do automatically
        """Update the button colors based on their enabled/disabled state."""
        BUTTON_ENABLED_COLOR = "white"
        BUTTON_DISABLED_COLOR = "grey"
        # Done Button Color
        if self.done_button.isEnabled():
            self.done_button.setStyleSheet("background-color: lightgreen; color: black;")
        else:
            self.done_button.setStyleSheet("background-color: lightgrey; color: black;")

        # Start Button Color
        if self.resume_button.isEnabled():
            self.resume_button.setStyleSheet("background-color: white; color: black;")
        else:
            self.resume_button.setStyleSheet("background-color: lightgrey; color: black;")

        # pause Button Color
        if self.pause_button.isEnabled():
            self.pause_button.setStyleSheet("background-color: white; color: black;")
        else:
            self.pause_button.setStyleSheet("background-color: lightgrey; color: black;")

        # extend Button Color
        if self.extend_button.isEnabled():
            self.extend_button.setStyleSheet("background-color: white; color: black;")
        else:
            self.extend_button.setStyleSheet("background-color: lightgrey; color: black;")

        if self.reduce_button.isEnabled():
            self.reduce_button.setStyleSheet("background-color: white; color: black;")
        else:
            self.reduce_button.setStyleSheet("background-color: lightgrey; color: black;")

        # Back Button Color
        if self.back_button.isEnabled():
            self.back_button.setStyleSheet("background-color: white; color: black;")
        else:
            self.back_button.setStyleSheet("background-color: lightgrey; color: black;")

        # Delete Button Color
        if self.delete_button.isEnabled():
            self.delete_button.setStyleSheet("background-color: white; color: black;")
        else:
            self.delete_button.setStyleSheet("background-color: lightgrey; color: black;")

    def pressed_back(self):
        logger.info("Back task triggered!")
        if self.current_task.task_previous is not None:
            self.current_task = self.current_task.task_previous
            logger.info(  f"Resetting; current_task is now {self.current_task.fullname}")
            if not self.timer_running:
                logger.info("Back  button pressed whilst timer paused; NOT restarting timer")
                #self.start_timer()

            self.reset_state_jumped_task()
            self.reset_UI()


    def pressed_done_next_task(self):
        logger.info("Next task triggered!")
        if self.current_task.task_previous is None and not self.timer_running: #Very beginning
            self.start_timer()
            logger.info("Kick off timing - first task triggered")
            self.done_button.setText("⏭️ Done")
            self.reset_UI()
            return


        if self.current_task.trigger_stream_list:
            for s in self.current_task.trigger_stream_list:
                try:
                    logger.info( f"Attempting to trigger stream {s.name} from task {self.current_task.fullname} !")
                    new_obj = self.__class__(s, self._parent_layout, auto_start = True, parent_instance = self.parent_instance)
                    self.triggered_Instances.append(new_obj)
                    self._parent_layout.addWidget(new_obj)
                    logger.info( f"Success: done trigger stream {s.name} from task {self.current_task.fullname} !")
                except ValueError as e:
                    logger.exception( f"Failed to trigger stream {s.name} from task {self.current_task.fullname} {e}!")
                except Exception as e:
                    logger.exception( f"Failed to trigger stream {s.name} from task {self.current_task.fullname} {e}!")

        if self.current_task.task_next is not None:
            self.current_task = self.current_task.task_next
            logger.info(  f"Resetting; current_task is now {self.current_task.fullname}")
            if not self.timer_running:
                logger.info("Done_Next button pressed whilst timer paused; restarting timer")
                self.start_timer()

            self.reset_state_jumped_task()
            self.reset_UI()
        else: #Final task is done for this strream 
            self.timer.stop()
            self.timer_running = False
            logger.error( f"Done  triggered on {self.current_task.name} - no following task so timer stopped!")
            self.update_button_states()
            self.update_timer_colour(grey = True)
            self.status_label.setText("*** Stream complete ***")


           
        
    def pressed_resume(self):
        logger.info("Resume button pressed; starting/restarting timer")
        self.start_timer()

    def start_timer(self):
        self.timer.start(1000)  # Start the timer with an interval of 1 second (but counting down every 5 seconds)
        self.timer_running = True
        self.resume_button.setText("▶️")
        self.update_button_states()
        self.update_status_label()

    def pressed_pause(self):
        self.timer.stop()
        self.timer_running = False #TODO - maybe have this a function that checks state of self.timer directly?
        self.status_label.setText(f" **** PAUSED *****")  
        self.update_button_states()
        self.live.pause_count += 1

    def pressed_extend(self):
        self.live.extend_count += 1
        self.live.remaining_time += 30  # Add 30 seconds to the timer
        self.update_status_label()
        self.update_timer_display(force_update = True)  # Force update the timer display

    def pressed_reduce(self):
        self.live.reduce_count += 1
        self.live.remaining_time -= 30  # Add 30 seconds to the timer
        self.update_status_label()
        self.update_timer_display(force_update = True)  # Force update the timer display


    def update_status_label(self):
        pause_plural="s" if self.live.pause_count != 1 else ""
        pause_msg=f"Paused {self.live.pause_count} time{pause_plural}" if self.live.pause_count>0 else ""

        extend_plural="s" if self.live.extend_count != 1 else ""
        extend_msg=f"Extended {self.live.extend_count} time{extend_plural}" if self.live.extend_count>0 else ""

        reduce_plural="s" if self.live.reduce_count != 1 else ""
        reduce_msg=f"Reduced {self.live.reduce_count} time{reduce_plural}" if self.live.reduce_count>0 else ""

        messages = [msg for msg in [pause_msg, extend_msg, reduce_msg] if msg]
        label =  " and ".join(messages)

        """
        if self.live.pause_count and self.live.snooze_count:
            label = f"Paused {self.live.pause_count} time{pause_plural} and snoozed: {self.live.snooze_count} time{snooze_plural}"
        elif self.live.pause_count:
            label = f"Paused {self.live.pause_count} time{pause_plural} "
        elif self.live.snooze_count:
            label = f"Snoozed: {self.live.snooze_count} time{snooze_plural}  "
        else:
            label = ""
        """

        self.status_label.setText( label  ) 
        self.update_timer_display()
        self.update_timer_colour()


    def pressed_close_stream(self):
        #self._parent_layout.removeWidget(self)
        #self._parent_layout.addWidget(self)
        # This method deletes the timer by removing it from the layout and deleting the object
        self.setParent(None)  # Remove the widget from the layout
        del self  # Delete the current instance


import weakref

class ChecklistExecution (QWidget):
    BG_COLOUR = "DarkGrey"
    _checklist_instances = weakref.WeakValueDictionary()  # Automatically removes unused instances

    def __new__(cls, checklist : Checklist, *args, **kwargs):
        logger.info(f"New checklist {checklist.name}")
        if checklist.name.lower().endswith("checklist"):
            if checklist.name in cls._checklist_instances:
                raise ValueError(f"A checklist instance with name '{checklist.name}' already exists!")
        instance = super().__new__(cls, checklist)
        cls._checklist_instances[checklist.name] = instance  # Store the new instance
        return instance
        

    def __init__(self, checklist : Checklist):
        super().__init__()   
        self.checklist = checklist
        self.init_UI()
        self.refresh()

    def pressed_close(self):
        # This method deletes the timer/checklist execution by removing it from the layout and deleting the object
        self.setParent(None)  # Remove the widget from the layout
        del self  # Delete the current instance
        
    def init_UI(self):
        self.setWindowTitle("Execution")
        self.setGeometry(100, 100, 1200, 800) #X, Y, WIDTH, HEIGHT

        # Layout
        self.layout = QVBoxLayout()

        # Create a QFrame (box) for both the title and description
        self.text_box_frame = QFrame(self)
        self.text_box_frame.setStyleSheet(f"border: 2px solid black; border-radius: 10px; padding: 10px; background-color: {self.BG_COLOUR};")
        self.layout.addWidget(self.text_box_frame)

        # Layout for the text box (title + description)
        text_box_layout = QVBoxLayout()

        # Title label inside the box
        self.title_label = QLabel(self.text_box_frame)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set a larger font for the title
        title_font = QFont("Arial", 16) 
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: black;")  
        text_box_layout.addWidget(self.title_label)

        # Description label inside the box (single-line)
        self.description_label = QLabel(self.text_box_frame)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description_font = QFont("Arial", 18)
        self.description_label.setFont(description_font)
        self.description_label.setStyleSheet("color: black; font-style: italic;")

        text_box_layout.addWidget(self.description_label)

        # Steps label inside the box (multi-line)
        steps_font = QFont( app.settings.value("fixed_font"), 18)
        self.steps_label = QTextEdit(self.text_box_frame)
        self.steps_label.setReadOnly(True)  
        self.steps_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steps_label.setFont(steps_font)
        self.steps_label.setTextColor(Qt.GlobalColor.black)
        font_metrics = QFontMetrics(self.steps_label.font())
        line_height = font_metrics.lineSpacing() 
        #self.steps_label.setMinimumHeight( int(10 * 12 * 1.5))  #roughly 10 rows but hardcoding of fontsize
        self.steps_label.setMinimumHeight( int(10 * line_height) + 22 ) #padding & border radius  

        text_box_layout.addWidget(self.steps_label)
        self.setLayout(self.layout)

        self.text_box_frame.setLayout(text_box_layout)


        self.delete_button = QPushButton("Hide Checklist", self)
        self.delete_button.setStyleSheet("color: black;")  
        self.delete_button.clicked.connect(self.pressed_close)
        self.delete_button.setEnabled(True)
        self.layout.addWidget(self.delete_button)

        # Tooltips for buttons
        self.delete_button.setToolTip("You can close this checklist at any time")

        # Initial state
        self.setLayout(self.layout)

    
    def refresh(self):
        #User feedback change -  remove "_" in checklist names (like streams/tasks)
        title=self.checklist.name.replace("_"," ")
        self.title_label.setText(title)
        self.description_label.setText(self.checklist.description)
        self.steps_text = ""
        for key in self.checklist.dictionary:
            if key !=  "Description" :
                value=Helper._get_strlist_from_dict(
                    self.checklist.dictionary, level1=key, default=[])
                self.steps_text += f"• {str(key)}\n"
                #TODO make a nice join
                self.steps_text += "\n".join(f"  • {v}" for v in value) 
                self.steps_text += "\n\n"
        if self.steps_text == "":
            self.steps_text = "[No steps defined; maybe it's obvious?]"

        self.steps_label.setPlainText(self.steps_text)  


class MainWindow(QMainWindow):
    def __init__(self, w : WorkflowStream):
        super().__init__()

        #init speaker
        self.speaker = None
        self.init_speaker()

        self.w = w
        self.setWindowTitle(w.name)
        self.setGeometry(100, 100, 1200, 500)

        self.menu_bar = QMenuBar(self)
        self.menu_window_menu = self.menu_bar.addMenu("Window")

        # Central widget + layout
        self.central = QWidget()
        self.main_layout = QVBoxLayout(self.central)

        # Create a layout for the timers
        #self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.menu_bar)  # Attach menu bar to QWidget


        self.preflight_button = QPushButton("Show Pre-Flight Checklist", self)
        self.preflight_button.setStyleSheet("color: black;")  
        self.preflight_button.clicked.connect(self.open_pre_checklist)
        self.main_layout.addWidget(self.preflight_button)

        # Create a layout for the timers themselves (side-by-side)
        self.timer_layout = QHBoxLayout()

        # Create the "Pre-flight" timer immediately
        self.open_pre_checklist()

        # Create the "Go" timer immediately
        self.timer1 = CountdownTimer(w.go_stream, self.timer_layout, auto_start = False, parent_instance=self)
        self.timer_layout.addWidget(self.timer1)

        # Add the layout to the main layout
        self.main_layout.addLayout(self.timer_layout)

        # Add the button to open Checklist
        self.postflight_button = QPushButton("Show Post-Flight Checklist", self)
        self.postflight_button.setStyleSheet("color: black;")  
        self.postflight_button.clicked.connect(self.open_post_checklist)
        self.main_layout.addWidget(self.postflight_button)

        # Status bar
        self.status = self.statusBar()
        # Status bar with two parts
        self.total_seconds = 0
        self.status_left = QLabel("0s")
        self.status_right = QLabel("Ready")
        self.status.addPermanentWidget(self.status_left) # always shown; cannot get pushed off
        self.status.addWidget(self.status_right)   # can be pushed off by other widgets in some situations

        #Now UI is setup
        self.setLayout(self.main_layout)
        self.setCentralWidget(self.central)



        # TODO - fix this
        # Start a timer to add a menu item dynamically after 30 seconds 
        #QTimer.singleShot(3000, self.add_dynamic_menu_items)

    def init_speaker(self):
        logger.info("Speaker init")
        self.temp_subfolder = tempfile.mkdtemp(prefix="audio_tts_")
        logger.info(f"Created cache folder {self.temp_subfolder}")
        # Set up audio worker in a thread; removed due to issues on older versions of macOS
        self.audio_thread = QThread() 
        self.speaker = Speaker(self.temp_subfolder)
        self.speaker.moveToThread(self.audio_thread)
        self.audio_thread.start()





    def add_dynamic_menu_items(self):
        logger.info("invoked to add window/streams menu")
        for index in range(0, len(self.w.stream_name_list)):
            logger.info( f"Adding menu items for index {index} = {self.w.stream_name_list[index]}" )
            new_action = QAction( f"Force Stream {self.w.stream_name_list[index]}", self)
            new_action.triggered.connect(lambda _, x=index: self.dynamic_function(x))  # Capture `index`
            self.menu_bar.addAction(new_action)


    def open_pre_checklist(self):
        try:
            logger.info("Opening Preflight Checklist")
            new_checklist=ChecklistExecution(w.pre_checklist)
            self.timer_layout.insertWidget(0,new_checklist) #force to the left
            logger.info("Opened Preflight Checklist and added it to self.timer_layout")
        except Exception as e:
            logger.exception("Error opening Preflight Checklist; duplicate? (e)")

    def open_post_checklist(self):
        try:
            logger.info("Opening Postflight Checklist")
            new_checklist=ChecklistExecution(w.post_checklist)
            self.timer_layout.addWidget(new_checklist)
            logger.info("Opened Postflight Checklist and added it to self.timer_layout")
        except Exception as e:
            logger.exception("Error opening Postflight Checklist; duplicate? (e)")




def show_critical_message(message: str, title: str = "Fatal Error"):
    """Display a critical message box that grabs focus."""
    logger.error("Critical_warning_box invoked")
    logger.error(f"Warning:{message}")
    logger.error(f"Title:{title}")

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setFocus()
    #msg.setWindowState()
    # Ensure it grabs focus
    msg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)  # Stay on top
    msg.setModal(True)  # Block input until closed
    msg.raise_()  # Bring to front
    msg.activateWindow()  # Activate focus
    if NSApplication:  # Bring to front 
        NSApp.activateIgnoringOtherApps_(True)

    
    # Alert the application (macOS fix)
    QApplication.alert(msg)
    sys.exit(1)


def critical_error(message: str):
    logger.fatal(message)
    msg = QMessageBox.critical(None, "Fatal", message, QMessageBox.StandardButton.Abort)
    if NSApplication:  # Bring to front 
        NSApp.activateIgnoringOtherApps_(True)
    
    logger.fatal("still here")
    sys.exit(1)

def handle_workflow_build_warnings(warnings : list =[]):
    if not warnings:
        return
     
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("Warning: Issues Detected in Workflow")
    
    # Format the warnings into a bullet-point list
    warnings_text = "\n".join(f"• {warning}" for warning in warnings)
    msg.setText(f"{warnings_text}\n\nDo you want to continue?")
    
    logger.error("Workflow_warnings invoked")
    logger.error(f"Warning:{warnings_text}")

    # Add Continue and Exit buttons
    msg.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
    exit_button = msg.addButton("Exit", QMessageBox.ButtonRole.RejectRole)

    # Show the message box and wait for response
    msg.exec()

    # Return based on user choice
    if msg.clickedButton() == exit_button:
        logger.error( f"User exited following {len(warnings)} warnings in build")
        sys.exit(1)
    logger.info( f"User chose to continue despite {len(warnings)} warnings in build")
    return
     


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.settings = QSettings("KatalinaM", "Timer")


    parser = argparse.ArgumentParser(description="Runs a workflow (typically a recipe) as part of the workflow ecosystem",    
            epilog="Note: Qt-specific arguments like '--style' and '-platform' can be used (advanced usage only).")

    # Define arguments
    parser.add_argument("filename", help="recipe/workflow in json/jsonc format (required)")
    parser.add_argument("-t", "--tick", type=int, help="Number of seconds to 'tick off' the remaining time every real second (optional)")

    args = parser.parse_args()
    if args.tick:
        app.settings.setValue("local_tick",args.tick)
    else:
        app.settings.setValue("local_tick",1)
        
    if not app.settings.value("fixed_font"):
        os_name = platform.system().lower()
        if  os_name == "darwin":
            app.settings.setValue("fixed_font", "Menlo")
        elif os_name == "windows":
            app.settings.setValue("fixed_font", "Consolas")
        else:
            app.settings.setValue("fixed_font", QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)   )

    logger.info(f"Processing workflow {args.filename}")
    try:
        with open(args.filename, "r") as file:
            recipe_dict = jsonc.load(file)
        w = WorkflowStream(args.filename, recipe_dict)
        logger.info(f"Loaded {w.name}; go_stream_name: {w.go_stream_name}")
    except OSError as e:
        logger.error( f"Uable to open Workflow file {args.filename}:\n{e}" )
        show_critical_message( f"Uable to open Workflow file {args.filename}:\n{e}" ) 
    except json.decoder.JSONDecodeError as e:
        critical_error(f"Uable to interpret Workflow file {args.filename}\nIt should be JSON/JSONC:\n{e}")
    warnings=w.build()
    handle_workflow_build_warnings(warnings)

    window = MainWindow(w)
    #User feedback change -  Start the application in fullscreen mode
    window.showFullScreen()  
    sys.exit(app.exec())

