"""A class that can log events in a permanent JSON file.
"""

import os
import json
import datetime
from typing import Any
from PathManager import PathManager

class LogManager:
    """Log reading, management and writing in/from a JSON file (log.json).

    Attributes:
        path: Path of the logfile to read/write.
        data: Runtime representation of the log as a dict: {"events": [..., ..., ...]}.
            Do not edit this variable manually during runtime. Use the log function instead.
    """

    def __init__(self):
        """Initializes the LogManager and reads/creates the data dict."""

        self.path = PathManager().get_data_path() + "/log.json"
        self.data = {}
        self.data["events"] = []
        if os.path.exists(self.path):
            self.read_log()

    def read_log(self):
        """Reads log from the log.json file into the data dict."""

        with open(self.path) as json_file:
            self.data = json.load(json_file)

    def save_log(self):
        """Writes contents of the data dict into the log.json file."""

        with open(self.path, 'w') as outfile:
            json.dump(self.data, outfile, indent=4)

    def log(self, log_obj: Any, log_type: str = "Standard"):
        """Logs the log_obj, adding the log_type and the current timestamp.

        Args:
            log_obj: The object to log. If it is not a dict, it will be turned into one: {"content": log_obj}.
            log_type: Optional; Can be used to classify a log event. If not specified: "Standard".
        """

        if not type(log_obj) == dict:
            log_obj = {"content": str(log_obj)}

        timestamp = str(datetime.datetime.now())
        log_obj["timestamp"] = timestamp
        log_obj["type"] = log_type

        self.data["events"].append(log_obj)
        self.save_log()