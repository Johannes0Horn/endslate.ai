"""A class that manages configurations/settings in a permanent JSON file.
"""

import os
import json
from PathManager import PathManager
from typing import Any

class ConfigManager:
    """Config reading, management and writing in/from a JSON file (config.json).

    Attributes:
        path: Path of the config file to read/write.
        data: Runtime representation of the config as a dict: {"port": 3333, "devices": [..., ...]}.
            Do not edit this variable manually during runtime. Use the set function instead.
    """

    def __init__(self):
        """Initializes the ConfigManager and reads/creates the data dict."""

        self.path = PathManager().get_data_path() + "/config.json"
        self.data = {}
        if os.path.exists(self.path):
            self.readConfig()

    def readConfig(self):
        """Reads config from the config.json file into the data dict."""

        with open(self.path) as json_file:
            self.data = json.load(json_file)

    def saveConfig(self):
        """Writes contents of the data dict into the config.json file."""

        with open(self.path, 'w') as outfile:
            json.dump(self.data, outfile, indent=4)

    def get(self, key: Any) -> Any:
        """Retrieves a setting.

        Args:
            key: The name of the setting to be retrieved.

        Returns:
            The value of the setting.
        """

        return self.data[str(key)]

    def set(self, key: Any, value: Any):
        """Sets a setting.

        Args:
            key: The name of the setting to be set.
            value: The value of the setting to be set.
        """

        self.data[str(key)] = value
        self.saveConfig()