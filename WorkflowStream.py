import logging
import jsonc, json
import sys
import typing

# pip install jsoncparser 
# source venv/bin/activate

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

#sample data for helper class
line='{"name": "Gilbert", "session": "2013", "score": 24, "completed": true}'
jsonc.loads(line)


# HELPER ##########################################################################################  

"""
This holds validations and other convenience functions.
There might well be cleverer ways to do these things using native python libraries.
By putting the logic here I can switch to the cleverer ways when I find them out.
"""
class Helper:
    NAME_RULES = "Alpha, Digit, underscore [_], fullstop [.] only"
    @staticmethod
    def _is_name_OK(name: str) -> bool:
        if not isinstance(name, str):
            logger.warning(f"name is not a string")
            return False
        for c in name:
            if not (c.isalpha() or c.isdigit() or c in ("_", ".")):
                logger.info(f"Not OK name '{name}")
                return False
        return True

    @staticmethod
    def _get_item_from_dict(
        dictionary: dict, level1: str, level2: str = "", default: typing.Any = None
    ) -> typing.Any:
        if not isinstance(dictionary, dict):
            logger.warning("invalid dictionary")
            return default

        if level1 is None or level1 == "" or not Helper._is_name_OK(level1):
            return default
        if level1 not in dictionary:
            return default
        if level2 is None or level2 == "":
            item = dictionary[level1]
        else:
            if (
                not isinstance(dictionary[level1], dict)
                or level2 not in dictionary[level1]
            ):
                return default
            item = dictionary[level1][level2]
        return item

    @staticmethod
    def _get_strlist_from_dict(
        dictionary: dict, level1: str, level2: str = "", default: list = []
    ) -> list:
        item = Helper._get_item_from_dict(dictionary, level1, level2, default)
        logger.debug(f"found list??? {item}  ")
        if item is None or item == "" or item == [] or item == default:
            return item
        item_list = []
        if isinstance(item, str):
            item_list.append(item)
            logger.warning(
                f"expected list but found str; converting to list {item_list}  "
            )
            return item_list
        if not isinstance(item, list) and not isinstance(item, jsonc.JSONCList):
            logger.warning(
                f"expected list but not list or str - returning default. Item is {item} / {type(item)} "
            )
            return default
        logger.debug(f"found & confirmed list {item}  ")
        for value in item:
            if isinstance(value, str):
                item_list.append(value)
            else:
                logger.warning(
                    f"expected list entry to be string; converting {value} to string and adding to list "
                )
                item_list.append(str(value))
        logger.debug(f"found & forced list of strings {item_list}  ")
        return item_list

    @staticmethod
    def _get_bool_from_dict(
        dictionary: dict, level1: str, level2: str = "", default: bool = False
    ) -> bool:
        item = Helper._get_item_from_dict(dictionary, level1, level2, default)
        logger.debug(f"found bool??? {item} / {type(item)}  ")
        if item is None or item == default:
            logger.debug(f"didn't seem to find  {level1}{level2} in dictionary  ")
            return item
        if isinstance(item, bool):
            logger.debug(f"found bool as expected '{item}'/ {type(item)}  ")
            return item
        logger.warning(
            f"expected bool but found {item} / {type(item)}; converting to bool "
        )
        item.Upper()
        if item == "FALSE":
            return False
        item = bool(
            item
        )  # TODO maybe too loose; anything other than 0, "0" or "" treated as True
        return item

    @staticmethod
    def _get_str_from_dict(
        dictionary: dict, level1: str, level2: str = "", default: str = ""
    ) -> str:
        item = Helper._get_item_from_dict(dictionary, level1, level2, default)
        logger.debug(f"found string??? {item}  ")
        if item is None or item == "" or item == default:
            logger.debug(f"didn't seem to find  {level1}{level2} in dictionary  ")
            return item
        if isinstance(item, str):
            logger.debug(f"found string as expected '{item}'  ")
            return item

        logger.warning(
            f"expected str but found {item} / {type(item)}; converting to string "
        )
        item = str(item)
        return item

    @staticmethod
    def _get_int_from_dict(
        dictionary: dict, level1: str, level2: str = "", default: int = 0
    ) -> int:
        location = f"{level1}/{level2}" if level2 != "" else level1
        item = Helper._get_item_from_dict(dictionary, level1, level2, default)
        if not isinstance(item, int):
            logger.debug(f" found int {item} at  {location} in dictionary - though maybe it's just default {default} ")
            return item
        if item is None:
            logger.debug(f"didn't seem to find int at {location} in dictionary; returning default {default}  ")
            return default
        try:
            converted_item = int(item)
            logger.debug(f"converted {item} at {location} in dictionary to int; returning {converted_item}  ")
            return converted_item
        except ValueError as e:
            logger.warning(f"unable to convert {item} at {location} in dictionary to int; returning default {default}  ")
        return default
    


# Live ##########################################################################################  
# A simple way to create additional keys or slots within a class
# In init, a class creates an instance of Live, and then it can get or assign variables to it.

class Live:
    def __init__(self):
        pass  # No predefined attributes; no restrictions (not using __slots__)



# TASK ##########################################################################################  


class Task:
    def __init__(self, name : str, dictionary : dict, parent_name : str =""):
        if not Helper._is_name_OK(name):
            logger.error(f"Invalid name for Task: {name}")
            raise ValueError(
                "Name of a Task must be a string containing A-Z 0-9 and _ only"
            )
        self.dictionary = dictionary
        self.name = name
        self.fullname = str(parent_name) + "/" + name if parent_name != "" else name #for debugging/logging
        self.task_next = None
        self.task_previous = None
        self.title = Helper._get_str_from_dict(
            self.dictionary, level1="Title", default=""
        )
        if self.title == "":    
            self.title = self.name.replace("_", " ")

        self.description = Helper._get_str_from_dict(
            self.dictionary, level1="Description", default=""
        )
        #User feedback - changed the default value 
        self.steps = Helper._get_strlist_from_dict(
            self.dictionary, level1="Steps", default=["No action needed here!"]
        )
        self.type = Helper._get_str_from_dict(
            self.dictionary, level1="Type", default="Background"
        )   
        if self.type not in ['Active', 'Background']:
            logger.warning(
                f"Task '{self.name}' has invalid type '{self.type}'; forcing to Background"
            )
            self.type = "Background"

        self.stakes = Helper._get_str_from_dict(
            self.dictionary, level1="Stakes", default="Low"
        )   
        if self.stakes not in ['Low', 'Medium', 'High' ]:
            logger.warning(
                f"Task '{self.name}' has invalid stakes '{self.stakes}'; forcing to Low"
            )
            self.stakes = "Low"

        self.Autoprogress = Helper._get_bool_from_dict(
            self.dictionary, level1="Autoprogress", default=False
        )   

        self.duration = Helper._get_int_from_dict(
            self.dictionary, level1="DurationSeconds", default=0
        )   

        self.StartMessage = Helper._get_str_from_dict(
            self.dictionary, level1="StartMessage", default=""
        )   

        self.CheckEverySeconds = Helper._get_int_from_dict(
            self.dictionary, level1="CheckEverySeconds", default=0
        )   

        self.CheckMessage = Helper._get_str_from_dict(
            self.dictionary, level1="CheckMessage", default=""
        )   

        if self.CheckEverySeconds <= 0 and self.CheckMessage != "":
            self.CheckEverySeconds = 60
            logger.warning(
                f"Task '{self.name}' has CheckMessage but no CheckEverySeconds; forcing to {self.CheckEverySeconds}"
            )

        if self.CheckEverySeconds > 0 and self.CheckMessage == "":
            self.CheckMessage = "Check"
            logger.warning(
                f"Task '{self.name}' has CheckEverySeconds of {self.CheckEverySeconds} but no CheckMessage; forcing to '{self.CheckMessage}'"
            )

        if self.Autoprogress and self.CheckEverySeconds > 0:
            self.Autoprogress = False
            logger.warning(
                f"Task '{self.name}' has CheckEverySeconds of {self.CheckEverySeconds} AND Autoprogress set; forcing Autoprogress to '{self.Autoprogress}'"
            )
   

        self.red = Helper._get_int_from_dict(
            self.dictionary, level1="Red", default=0
        )   
        self.amber = Helper._get_int_from_dict(
            self.dictionary, level1="Amber", default=0
        )   
        self.green = Helper._get_int_from_dict(
            self.dictionary, level1="Green", default=0
        )   
        self.trigger_stream_namelist = Helper._get_strlist_from_dict(
            self.dictionary, level1="Trigger", default=[]
        )
        self.trigger_stream_list = []

    def _link_triggered_stream(
        self, triggered_stream
    ):  # this is called by Workflow since only Workflow knows about other Streams
        # could validate that
        print(
            f"I've been asked to link myself - Task {self.fullname} to Stream {triggered_stream.name}"
        )
        if triggered_stream in self.trigger_stream_list:
            warning = f"Task '{self.fullname}' is already linked to Stream {triggered_stream.name}"
            logger.warning(warning)
            return  # could raise an exception but why?
        if triggered_stream.name not in self.trigger_stream_namelist:
            warning = f"Task '{self.fullname}' is not supposed to be linked to stream_name '{triggered_stream.name}'; my list is {self.trigger_stream_namelist}"
            logger.error(warning)
            raise IndexError(   warning         ) 
        self.trigger_stream_list.append(triggered_stream)
        return


# CHECKLIST #############################################################################

class Checklist:
    def __init__(self, name, dictionary):
        if not Helper._is_name_OK(name):
            logger.error(f"Invalid name for Checklist: {name}")
            raise ValueError(
                "Name of a Checklist must be a string containing A-Z 0-9 and _ only"
            )
        self.dictionary = dictionary
        self.name = name
        self.title = name
        self.description = Helper._get_str_from_dict(self.dictionary, "Description", default= f"This is the {name} ")

# STREAM #############################################################################


class Stream:
    def __init__(self, name, dictionary):
        if not Helper._is_name_OK(name):
            logger.error(f"Invalid name for Stream: {name}")
            raise ValueError(
                "Name of a Stream must be a string containing A-Z 0-9 and _ only"
            )
        self.dictionary = dictionary
        self.name = name
        self.task_list = []
        self.task_name_map = {} #needed to check task names are unique within the stream and to enable x-stream linking
        self.resolved_tasks = False
        self.trigger_stream_name_map = {}
        self.resolved_triggered_streams = False
        self.title = Helper._get_str_from_dict(
            self.dictionary, level1="Settings", level2="Title", default=self.name
        )
        self.column = Helper._get_str_from_dict(
            self.dictionary, level1="Settings", level2="DisplayColumn", default=None
        )
        self.countdown = Helper._get_str_from_dict(
            self.dictionary, level1="Settings", level2="CountDown", default=True
        )
        self.build_warnings=[] #if we have any issues, a higher level UI can report to user 

    def __iter__(self):
        """Allows enumeration by iterating over task_list."""
        return iter(self.task_list)

    def __getitem__(self, index):
        """Allows indexing by forwarding to task_list[index]."""
        return self.task_list[index]
    
    def __str__(self):
        return f"Stream: {self.name}"

    def __repr__(self):
        return f'Stream("{self.dictionary}")'


    def resolve_tasks(self)->list: 
        first=True
        for task_name in self.dictionary: 
            logger.info(
                f"Stream {self.name} potentially adding task with label {task_name}"
            )
            if task_name == "Settings":
                continue #already processed Settings section
            elif task_name in self.task_name_map:
                warning=f"Task '{task_name}' in Stream '{self.name}' is duplicated; only processed first"
                logger.warning(warning)
                self.build_warnings.append(warning)
            elif not isinstance(self.dictionary, dict):
                warning=f"Task '{task_name}' in Stream '{self.name}' is not a valid 'dictionary'; ignoring"
                logger.warning(warning)
                self.build_warnings.append(warning)
            else: 
                task_dictionary = self.dictionary[task_name] #this is JSON defining the task
                task = Task(task_name, task_dictionary, parent_name = self.name)
                self.task_list.append(task)
                self.task_name_map[task_name] = task  #needed later to do x-stream links
                if first:
                    self.task_first=task
                    first=False
                    task_previous = task
                else:
                    task.task_previous = task_previous
                    task_previous.task_next = task
                    task_previous = task
                logger.info(f"Stream {self.name} added task with label {task_name}")
        return self.build_warnings

        
    # check any tasks in this stream trigger any other streams and link them to the Stream reference
    #returns list of build errors rather than an exception
    def resolve_triggered_streams(self, stream_name_to_stream_reference_map) -> list:
        warnings=[]  
        if self.resolved_triggered_streams:  # only want to do this once
            return
        task = self.task_first
        dup_check={}
        while task is not None:
            if task.trigger_stream_namelist:
                info = f"Found triggered_streams {task.trigger_stream_namelist} in task  '{self.name}/{task.name}' "
                logger.info(info)
                print(info)

                for trigger_stream_name in task.trigger_stream_namelist:
                    if trigger_stream_name not in stream_name_to_stream_reference_map.keys():
                        warning= f"Unknown Stream '{trigger_stream_name}' in task  '{self.name}/{task.name}' "    
                        logger.warning(warning)
                        warnings.append(warning) 
                    elif trigger_stream_name in dup_check:
                        warning= f"Duplicate trigger for Stream '{trigger_stream_name} within Stream '{self.name} in task '{task.name}'; first trigger was in task {dup_check[trigger_stream_name]}"    
                        logger.warning(warning)
                        warnings.append(warning)
                    else:
                        dup_check[trigger_stream_name]=task.name
                        trigger_stream = stream_name_to_stream_reference_map[trigger_stream_name]
                        info = f"Linking task'{self.name}/{task.name}' to {trigger_stream_name}"
                        logger.info(info)
                        print(info)
                        info = f"Linking task'{self.name}/{task.name}' to {trigger_stream.name}"
                        logger.info(info)
                        print(info)
                        task.trigger_stream_list.append( trigger_stream )
                #self.trigger_stream_name_map[task.name] = task.trigger_stream_namelist
            task = task.task_next
        self.resolved_triggered_streams = True
        return warnings

    def iterator_visualiser(self,row, chain_set=set()):
        #yield type_string = "Stream/Task", name, column=(Middle/Left/Right),row=0, reference
        #yield "Stream", self.go_stream.name, self.go_stream.column, 0, self.go_stream
        in_row = row
        warning=f"display; Stream/self.name {self.name} row:'{row}' chain_set:{chain_set}"
        logger.info(warning)
        if self.name in chain_set:
            warning=f"Workflow is not a DAG; we have cycled back to Stream '{self.name} via {chain_set}"
            logger.error(warning)
            return
        chain_set.add(self.name)
        for task in self.task_list:
            yield "Task", task.name, self.column, row, task
            row += 1
        #yield type_string = "Stream/Task", name, column=(Middle/Left/Right),row=0, reference
        #yield "Stream", self.go_stream.name, self.go_stream.column, 0, self.go_stream

        row = in_row  #arrow starts at the triggering task's row and goes to the triggered stream's column
        for task in self.task_list:         
            for triggered_stream in task.trigger_stream_list:
                print(f"yielding trigger itself {task.name} to {triggered_stream.name}")
                yield "Trigger", f"{self.name}/{task.name}->{triggered_stream.name}", triggered_stream.column, row, triggered_stream
                row += 1
                print(f"yielding triggered stream {triggered_stream.name}")
                yield "Stream", triggered_stream.name, triggered_stream.column, row, triggered_stream
                row += 1
                for yielded_type_string, yielded_name, yielded_column, yielded_row, yielded_reference in triggered_stream.iterator_visualiser( row, chain_set):
                    yield yielded_type_string, yielded_name, yielded_column, yielded_row, yielded_reference
                row += 1



    def iterator(self):
        column=1
        yield "Stream", self.name, self
        for task in self.task_list:
            yield "Task", task.name, task
            for triggered_stream in task.trigger_stream_list:
                yield "TriggeredStream", triggered_stream.name, triggered_stream


    def iter_names(self, recurse=False):
        task = self.task_first
        while task:
            if task.trigger_stream_namelist != []:
                for triggered_stream_name in task.trigger_stream_namelist:
                    yield "Stream", triggered_stream_name
                '''for triggered_stream in task.trigger_stream_list:
                    yield "Stream", triggered_stream.name'''
            yield "Task", task.name
            task=task.task_next


    def display(self, chain="", chain_set=set() ):
        warning=f"display; Stream/self.name {self.name} chain:'{chain}' chain_set:{chain_set}"
        logger.info(warning)
        if self.name in chain_set:
            warning=f"Workflow is not a DAG; we have cycled back to Stream '{self.name} via {chain_set}"
            logger.error(warning)
            return
        chain_set.add(self.name)
        in_chain = chain
        chain = f"{in_chain}[Stream:{self.name}]"
        task = self.task_first
        while task:
            chain = f"{chain} -> {task.name}"
            task = task.task_next
        print(chain)
        # walk the list again, recursing into any triggered_streams; TODO should check chain to see if already recursed into this Stream
        chain = f"{in_chain}[Stream:{self.name}]"
        task = self.task_first
        while task:
            chain = f"{chain} -> {task.name}"
            if task.trigger_stream_list != []:
                for triggered_stream in task.trigger_stream_list:
                    print(f"displaying triggered stream {triggered_stream.name}")
                    chain2 = f"{chain} -> "
                    triggered_stream.display(chain = chain2, chain_set= chain_set)
            task = task.task_next


# WORKFLOW_STREAM #############################################################################

class WorkflowStream:
    def __init__(self, name, dictionary):
        self.dictionary = dictionary
        self.go_stream = None
        self.pre_checklist = None
        self.post_checklist = None
        self.go_stream_name = Helper._get_str_from_dict(
            self.dictionary, "GoStream", default=None
        )
        self.invoked_name = name
        self.name = Helper._get_str_from_dict(
            self.dictionary, "Identity", "Name", default=self.invoked_name
        )
        failed = self._initial_validation()
        if failed:
            raise ValueError(
                f"Unable to build WorkflowStream due to invalid Workflow/Recipe\n{str(failed)}"
            )
        #Pre/Post checklists
        if "PreFlight" in self.dictionary:
            if not isinstance(self.dictionary["PreFlight"], dict):
                logger.error(f"Unable to process PreFlight checklist")
            else:
                self.pre_checklist = Checklist("PreFlight_checklist",self.dictionary["PreFlight"])
        if "PostFlight" in self.dictionary:
            if not isinstance(self.dictionary["PostFlight"], dict):
                logger.error(f"Unable to process PostFlight checklist")
            else:
                self.post_checklist = Checklist("PostFlight_checklist",self.dictionary["PostFlight"])

        #Streams
        self.stream_name_to_stream_reference_map = {}
        self.stream_list = []
        self.stream_name_list = [] 
        self.column_stream_map = {}
        for stream_name in self.dictionary["Streams"]:
            if not Helper._is_name_OK(stream_name):
                warning = f"Invalid Stream name '{stream_name}' in Workflow '{self.name}'"
                logger.error(warning)
                raise ValueError(warning)
            if stream_name in self.stream_name_to_stream_reference_map:
                warning = f"Duplicate Stream name '{stream_name}' in Workflow '{self.name}'"
                logger.error(warning)
                raise ValueError(warning)
            stream = Stream(stream_name, self.dictionary["Streams"][stream_name])
            self.stream_name_to_stream_reference_map[stream_name]=stream
            self.stream_list.append(stream)
            self.stream_name_list.append(stream_name)
            if stream_name == self.go_stream_name:
                self.go_stream = stream
        self.state = "Init"

    # In Init state (after __init__() ), the tasks and streams are shallow
    # Build goes through and links everything up
    # This is where "compile errors" will be found and should be reported to user
    # We want to avoid init failing with the first weird issue found, since this stops the whole workflow
    def build(self):  
        if self.state != "Init":
            logger.warning(
                f"build() called on Workflow '{self.name}'when workflow not in Init state; state is ;{self.state}"
            )
            return
        warnings=[]
        work_stream_warnings=set()
        self._build_columns()
        for stream in self.stream_list:
            w = stream.resolve_tasks() 
            if w != []:
                warnings.append(w)  #TODO check warnings here?
                work_stream_warnings.add(stream.name)
        # the tasks now know the name of the 0+ streams they link to
        # Stream and task don't know the mapping of stream names to the object references
        # Workflow needs to pass the mapping to each stream so the stream can apply the link from task to the actual object
        # 
        for stream in self.stream_list:
            w = stream.resolve_triggered_streams( self.stream_name_to_stream_reference_map )
            if w != []:
                warnings.append(w)  #TODO check warnings here?
                work_stream_warnings.add(stream.name)
        self.state = "Built"
        if work_stream_warnings:
            warnings.insert (0, f"Errors in Streams {work_stream_warnings}")
        return warnings

    def display(self):
        if self.state != "Built":
            logger.warning(
                f"display() called on Workflow when workflow not in Built state; state is ;{self.state}"
            )
            return
        print(f"\n---------\nWorkstream '{self.name:}'")
        print("[PreFlight]")
        self.go_stream.display()
        print("[PostFlight]")

    def iterator_visualiser(self):
        #yield type_string = "Stream/Task", name, column=(Middle/Left/Right),row=0, reference
        #Need to return Pre-Flight
        row=0
        if self.pre_checklist:
            logger.debug( f"viz: yielding PrePostStream: {self.pre_checklist.name}")
            yield "PrePostStream", "Preflight Checklist", "Left", row, self.pre_checklist
            row+=1
        max_row = row

        logger.debug( f"viz: yielding go_stream, {self.go_stream_name}")
        yield "Stream", self.go_stream.name, self.go_stream.column, row, self.go_stream
        #yield "Task", self.go_stream.name, self.go_stream.column, 5, self.go_stream
      
        for type_string, name, column, row, reference in self.go_stream.iterator_visualiser(row=2):
            logger.debug( f"viz: yielding workflow, name:{name} column:{column} row:{row}")
            yield type_string, name, column, row, reference
            if row>max_row:
                max_row = row
        if self.post_checklist:
            max_row += 1
            logger.debug( f"viz: yielding PrePostStream: {self.post_checklist.name}")
            yield "PrePostStream", "Postflight Checklist", "Left", max_row, self.post_checklist


    def iterator(self):
        #yield type_string=""
        for type_string, name, reference in self.go_stream.iterator():
            yield type_string, name, reference


    def _build_columns(
        self,
    ):  # broken out from init for simplicity and to reduce chance of a general __init__ failure
        self.go_stream.column = 1
        next_col=2
        for stream in self.stream_list:
            if stream != self.go_stream:
                stream.column = next_col
                next_col += 1
        logger.info("Depcrecated function - build_columns")
        return
        self.column_positions = {"Left": 100, "Middle": 400, "Right": 700}
        for stream in self.stream_list:
            if stream.column is None or stream.column=="":
                warning=f"Stream '{stream.name}' has no column defined"
                logger.error(warning)
                raise ValueError(warning)
            
            elif stream.column not in self.column_positions:
                warning=f"Stream {stream.name} has invalid column '{stream.column}' defined"
                logger.error(warning)
                raise ValueError(warning)
        
            elif stream.column in self.column_stream_map:
                dup_stream_name = self.column_stream_map[stream.column]
                warning=f"Stream {stream.name} and Stream {dup_stream_name} both request column {stream.column}"
                logger.error(warning)
                raise ValueError(warning)
            else:
                self.column_stream_map[stream.column] = stream.name


    def _initial_validation(self):
        failed = []
        mandatorySections = [
            "Identity",
            "GoStream",
            "PreFlight",
            "PostFlight",
            "Streams",
        ]
        for section in mandatorySections:
            if not section in self.dictionary:
                failed.append(f"Recipe missing section '{section}'")
                return failed
        if self.go_stream_name not in self.dictionary["Streams"]:
            logger.error(
                f"Unable to find GoStream '{self.go_stream_name}' in the Streams section"
            )
            failed.append(
                f"Unable to find GoStream '{self.go_stream_name}' in the Streams section"
            )
        for stream_name in self.dictionary["Streams"]:
            if not Helper._is_name_OK(stream_name):
                logger.error(f"Invalid name for a Stream: '{stream_name}'")
                failed.append(
                    f"Stream name '{stream_name}' is not a valid name; Name of a Stream must be a string containing A-Z 0-9 and _ only"
                )
            stream = self.dictionary["Streams"][stream_name]
            if stream is None:
                failed.append(
                    f"Stream '{self.stream_name}' in the Streams section is empty"
                )
            elif not isinstance(stream, dict):
                failed.append(
                    f" Stream '{stream_name}' in the Streams sections is  invalid - it should be a dictionary"
                )

        return failed

    def check_workflow_for_issues(self)->list:
        return []
        # TODO check all streams are visited



if __name__ == "__main__":
    print("----\nIn main\n")


    # HELPER ##########################################################################################  

    logger.info("A bunch of checks/demos on HELPER class")
    logger.info("---------------------------------------")

    #sample data for helper class
    line = '{"name": "Gilbert", "session": "2013", "score": 24, "completed": true}'
    dictionary = jsonc.loads(line)

    item = Helper._get_str_from_dict(dictionary, "name")
    print(item)
    item = Helper._get_str_from_dict(dictionary, "score")
    print(item)

    line = '{"name": "Gilbert", "session": "2013", "score": 24, "completed": true, "info" : {"info2" : "interesting", "infonum" : 5}}'
    dictionary = jsonc.loads(line)

    item = Helper._get_str_from_dict(dictionary, "name")
    print(item)
    item = Helper._get_str_from_dict(dictionary, "score")
    print(item)
    item = Helper._get_str_from_dict(dictionary, "info", "info2")
    print(item)
    item = Helper._get_str_from_dict(dictionary, "info", "infonum")
    print(item)
    item = Helper._get_str_from_dict(dictionary, "info", "infomissing")
    print(item)
    item = Helper._get_str_from_dict(dictionary, "info", "infomissing", default="defaulted")
    print(item)

    #slightly better check; should maybe use proper TDD
    item = Helper._get_int_from_dict(dictionary, "info", "infomissing", default=-1)
    print(  f"*** Got {item} should be int {isinstance(item,int)} with matching default of -1 {item == -1} ")

    item = Helper._get_int_from_dict(dictionary, "score", default=-1)
    print(  f"*** Got {item} should be int {isinstance(item,int)} with value 24 {item == 24} ")


    line = '{ "Steps" : ["Pour the water into the Kettle", "Close lid", "Turn on"]}'
    dictionary = jsonc.loads(line)
    item = Helper._get_strlist_from_dict(dictionary, "Steps")
    print("Steps", item)


    print("22", Helper._is_name_OK(22))
    print('"22"', Helper._is_name_OK("22"))
    print('"Hello_World"', Helper._is_name_OK("Hello_World"))
    print('"Hello-World"', Helper._is_name_OK("Hello-World"))

    print('"Hello World"', Helper._is_name_OK("Hello World"))
    print('"Hello:World"', Helper._is_name_OK("Hello:World"))
    print('"None"', Helper._is_name_OK(None))




    # TASK ##########################################################################################  
    task_json = """{
                    "Title" : "Boil kettle",
                    "Description" : "Click Done when boiled",
                    "Steps" : ["Pour the water into the Kettle", "Close lid", "Turn on"],
                    "DurationSeconds" : 120,
                    "Green" : 80,
                    "Amber" : 120,
                    "Red" : 150,
                    "CheckSeverity" : "Low", 
                    "CheckMessage" : "Water Boiling?"
                }"""

    task_dict = jsonc.loads(task_json)
    task = Task("test", task_dict)
    print(task, type(task))
    print("task.name", task.name, type(task.name))
    print("task.steps", task.steps, type(task.steps))
    print("task.description", task.description, type(task.description))
    print(
        "task.trigger_stream_namelist",
        task.trigger_stream_namelist,
        type(task.trigger_stream_namelist),
    )

    print("\n---\ntask.dictionary", task.dictionary, type(task.dictionary))


    task_json = """
    {
                    "Title" : "Put eggs into pan",
                    "Description" : "We're going to boil eggs carefully - click done when all eggs are in the pan so we time correctly",
                    "Steps" : ["Pour boiling water into pan carefully", "Put pan on a safe burner (normally at back", "Set temperature so that water simmers", "Using the spatula, place each egg into the water"],
                    "Green" : 30,
                    "Amber" : 60,
                    "Red" : 90,
                    "DurationSeconds" : 60,         
                    "CheckSeverity" : "Low", 
                    "CheckMessage" : "Eggs in pan?",
                    "Trigger" : "ToastStream"
                }"""

    print("\n---\n task stuff #1A")


    task_dict = jsonc.loads(task_json)
    task = Task("test_trigger", task_dict)
    print(task, type(task))
    print("task.name", task.name, type(task.name))
    print("task.steps", task.steps, type(task.steps))
    print("task.description", task.description, type(task.description))
    print(
        "task.trigger_stream_namelist",
        task.trigger_stream_namelist,
        type(task.trigger_stream_namelist),
    )

    print("\n---\ntask.dictionary", task.dictionary, type(task.dictionary))
    result = Helper._get_strlist_from_dict(task.dictionary, "Trigger", default=[])
    print("trigger result", result)



    # STREAM #############################################################################


    stream_json = """
    {
                "Settings" : {
                    "Title" : "Eggs",
                    "DisplayColumn" : "Left",
                    "AlwaysDisplay" : false,
                    "CountDown" : true
                },
                "Boil" : {
                    "Title" : "Boil kettle",
                    "Description" : "Click Done when boiled",
                    "Steps" : ["Pour the water into the Kettle", "Close lid", "Turn on"],
                    "DurationSeconds" : 120,
                    "Green" : 80,
                    "Amber" : 120,
                    "Red" : 150,
                    "CheckSeverity" : "Low", 
                    "CheckMessage" : "Water Boiling?"
                },
                "PlaceEggs" : {
                    "Title" : "Put eggs into pan",
                    "Description" : "We're going to boil eggs carefully - click done when all eggs are in the pan so we time correctly",
                    "Steps" : ["Pour boiling water into pan carefully", "Put pan on a safe burner (normally at back", "Set temperature so that water simmers", "Using the spatula, place each egg into the water"],
                    "Green" : 30,
                    "Amber" : 60,
                    "Red" : 90,
                    "DurationSeconds" : 60,         
                    "CheckSeverity" : "Low", 
                    "CheckMessage" : "Eggs in pan?",
                    "Trigger" : "ToastStream"
                },
                "MonitorWater" : {
                    "Title" : "Monitor Boiling Water",
                    "Description" : "Let's keep an eye on pan, reduce heat if water might boil over",
                    "CheckEverySeconds" : 45,
                    "CheckMessage" : "Water OK?",
                    "CheckSeverity" : "Low",
                    "DurationSeconds" : 120,
                    "Autoprogress" : true 
                },
                "RemoveEggs" : {
                    "Title" : "Remove eggs carefully then hit Done",
                    "Column" : "left", 
                    "Description" : null,
                    "Steps" : ["Turn off burner", "Using the spatula, take each egg from water and place in bowl"],
                    "Green" : 30,
                    "Amber" : 45,
                    "Red" : 90,
                    "DurationSeconds" : 45,         
                    "DurationOverrunMessage" : "Eggs still in pan?",
                    "DurationOverrunSeverity" : "Medium"
                }
            }
    """


    print("\n---\nstream stuff #1")

    stream_dict = jsonc.loads(stream_json)
    stream = Stream("test", stream_dict)
    print(stream, type(stream))
    print("stream.name", stream.name, type(stream.name))
    print("stream.countdown", stream.countdown, type(stream.countdown))
    print("\n---\nstream.dictionary", stream.dictionary, type(stream.dictionary))

    print("\n---\nstream.resolve_tasks")
    stream.resolve_tasks()
    print("stream.task_name_map.keys()", stream.task_name_map.keys())


    print("\n---\nstream.resolve_tasks")
    stream.resolve_tasks()
    print("\n---\nstream.resolve_triggered_streams")
    warnings = stream.resolve_triggered_streams({})
    print(warnings)


    print("----\nResult of iter_names stream1\n*****\n")
    for node_type, name in stream.iter_names():
        print( node_type, name )


    stream_json = """
    {
                "Settings" : {
                    "Title" : "Eggs",
                    "DisplayColumn" : "Left",
                    "AlwaysDisplay" : false,
                    "CountDown" : true
                },
                "Boil" : {
                    "Title" : "Boil kettle",
                    "Description" : "Click Done when boiled",
                    "Steps" : ["Pour the water into the Kettle", "Close lid", "Turn on"],
                    "DurationSeconds" : 120,
                    "Green" : 80,
                    "Amber" : 120,
                    "Red" : 150,
                    "CheckSeverity" : "Low", 
                    "CheckMessage" : "Water Boiling?"
                }
    }
                """

    print("\n---\nstream stuff #2")

    stream_dict = jsonc.loads(stream_json)
    stream = Stream("test", stream_dict)
    print(stream, type(stream))
    print("stream.name", stream.name, type(stream.name))
    print("stream.countdown", stream.countdown, type(stream.countdown))
    print("\n---\nstream.dictionary", stream.dictionary, type(stream.dictionary))


    print("\n---\nstream.resolve_tasks")
    stream.resolve_tasks()
    print("\n---\nstream.resolve_triggered_streams")
    warnings = stream.resolve_triggered_streams({})
    print(warnings)


    print("----\nResult of iter_names stream2\n*****\n")
    for node_type, name in stream.iter_names():
        print( node_type, name )

    print("----\nEnd of Result of iter_names stream2\n*****\n")



    # WORKFLOW_STREAM #############################################################################

    file_name = r"recipes/recipe-simple.jsonc"
    try:
        with open(file_name, "r") as file:
            recipe_dict = jsonc.load(file)
        w = WorkflowStream(file_name, recipe_dict)
        print("w.go_stream_name", w.go_stream_name)
    except OSError as e:
        print(f"Uable to open Workflow file {file_name}:\n{e}")
    except json.decoder.JSONDecodeError as e:
        print(f"Uable to interpret Workflow file {file_name}:\n{e}")
    warnings=w.build()
    if warnings!=[]:
        print("Warnings building workflow from {file_name}")
        print(warnings)
    warnings=w.check_workflow_for_issues()
    if warnings!=[]:
        print("Warnings checking workflow from {file_name}")
        print(warnings)

    w.display()

    print("----\nIn main\n")
    file_name = "recipes/recipe-with-set-streams.jsonc"
    try:
        with open(file_name, "r") as file:
            recipe_dict = jsonc.load(file)
        w2 = WorkflowStream(file_name, recipe_dict)
        print("w2.go_stream_name", w2.go_stream_name)
    except OSError as e:
        print(f"Uable to open Workflow file {file_name}:\n{e}")
    except json.decoder.JSONDecodeError as e:
        print(f"Uable to interpret Workflow file {file_name}:\n{e}")
    warnings=w2.build()
    if warnings!=[]:
        print("Warnings building workflow from {file_name}")
        print(warnings)
    warnings=w2.check_workflow_for_issues()
    if warnings!=[]:
        print("Warnings checking workflow from {file_name}")
        print(warnings)
    w2.display()
    print("-----\nw2 iterator\n-----")
    for type_string, name, reference in w2.iterator():
        print (type_string, name, reference.name, type(reference))


