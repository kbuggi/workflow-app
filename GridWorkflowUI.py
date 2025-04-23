#Grid WorkflowStream

import logging

import sys

import json, jsonc

from WorkflowStream import WorkflowStream, Stream, Task

from GridUI import GridController

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import QSettings
import argparse


# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)




if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.settings = QSettings("KatalinaM", "Timer")


    parser = argparse.ArgumentParser(description="Shows a workflow (typically a recipe) as part of the workflow ecosystem",    
            epilog="Note: Qt-specific arguments like '--style' and '-platform' can be used (advanced usage only).")

    # Define arguments
    parser.add_argument("filename", help="recipe/workflow in json/jsonc format (required)")

    args = parser.parse_args()
        
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
        w2 = WorkflowStream(args.filename, recipe_dict)
        print("w2.go_stream_name", w2.go_stream_name)
    except OSError as e:
        print(f"Uable to open Workflow file {args.filename}:\n{e}")
    except json.decoder.JSONDecodeError as e:
        print(f"Uable to interpret Workflow file {args.filename}:\n{e}")
    warnings=w2.build()
    if warnings!=[]:
        print("Warnings building workflow from {args.filename}")
        print(warnings)
    warnings=w2.check_workflow_for_issues()
    if warnings!=[]:
        print("Warnings checking workflow from {args.filename}")
        print(warnings)
    w2.display()
    print("-----\nw2 iterator\n-----")
    #             yield "Task", task.name, self.column, row, task



    controller = GridController(w2.name)

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


    controller.show()



    for type_string, name, column, row, reference in w2.iterator_visualiser():
        logger.info( f"viz: type_string:{type_string} name:{name} column:{column} row:{row}")
        #set defaults for each cell; type-specific settings will override
        width=1
        text_colour=Qt.GlobalColor.black
        if hasattr(reference, "title") and reference.title != "":
            label=reference.title
        else:
            label = name
        if hasattr(reference, "dictionary"): 
            dictionary = reference.dictionary
        else:
            dictionary={}
        if type_string == "Stream":
            dictionary = {"Stream" : name}
            background_colour=Qt.GlobalColor.darkMagenta
        #User suggestion : show more about task in the viewer
        elif type_string == "Task":
            if reference.type == "Active":
                background_colour=Qt.GlobalColor.white
            else:
                background_colour=Qt.GlobalColor.darkGray
            if reference.Autoprogress:
                label += "" #TODO - pick an emoji 
            if reference.CheckMessage or reference.StartMessage:
                label += " ‼️" #indicates speech


        elif type_string == "PrePostStream":
            background_colour=Qt.GlobalColor.darkCyan
            text_colour=Qt.GlobalColor.white
            width=3
        elif type_string == "Trigger":
            background_colour=Qt.GlobalColor.black
            label = "↘️"
            dictionary = {"trigger" : name}
        else:
            print()
            logger.error(f"Unknown type: '{type_string}' for workflow item '{name}'; unable to visualize it properly")

        controller.populate_cell(column, row, width, text_colour, background_colour, label, dictionary)

    controller.reset_window_height() # resize window to show all rows (if possible)

    sys.exit(app.exec())
