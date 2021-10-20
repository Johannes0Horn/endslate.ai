"""A class that handles websocket port usage to communicate with extensions.
"""

import os
from ConfigManager import ConfigManager

class PortManager:
    """Port management for communicating with extensions.

    To communicate with Enslate.AI extensions we use websockets. This class contains methods that handle
    the determination of the port that will be used for these communications.

    Attributes:
        port: The port being used at the moment, either an int or None. It is not recommended to access the variable
            from outside the class. Use get_port instead.
        config: The configuration object of this instance of the backend, used to read/write permanent port.
    """

    def __init__(self, config: ConfigManager, port: int = None):
        """Initializes the PortManager with a ConfigManager and an optional port.

        Args:
            config: The ConfigManager to be used to read/write port from config.json.
            port: Optional; Can be set if the use of a specific port is required.
        """

        self.port = port
        self.config = config

    def is_port_in_use(self) -> bool:
        """Tries to connect to a port to test whether it is free to use.

        Returns:
            True if the port is free. Otherwise false.
        """

        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', self.port)) == 0

    def find_free_port(self) -> int:
        """Searches for a free port to use.

        Tests up to 100 possible consecutive ports starting at 3333. The first found free port is saved inside class
        and written to the ConfigManager.

        Returns:
            The first port found to be free.
        """

        self.port = 3333 if self.port == None else self.port

        for x in range(100):
            if self.is_port_in_use():
                self.port += 1
            else:
                print("found free port: ", self.port)
                break

        self.config.set("port", self.port)
        return self.port

    def get_port(self) -> int:
        """Systematically looks for a port to use.

        If port is already set, it will be returned immediately.
        If there is a port saved in the config file, it will be tested and returned if it is still free.
        If there is no saved port in the config or the saved port is occupied, a new port will be found.
        Visualization: https://endslate-ai.atlassian.net/l/c/yJT5qyJ3 .

        Returns:
            The port to be used.
        """

        if self.port != None:
            return self.port

        try:
            self.port = int(self.config.get("port"))
            if self.is_port_in_use():
                print("saved port in use, use new free port and save to settings")
                self.find_free_port()
            else:
                print("saved port not in use. Using saved Port ", self.port)
        except:
            print("no port saved, choose new port and safe to setting file")
            self.find_free_port()

        return self.port