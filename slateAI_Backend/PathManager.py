"""A class that handles path construction.
"""

import sys, os
from sys import platform as _platform

class PathManager:
    """Functions for retrieving system dependant paths."""

    def __init__(self):
        """Empty initialization."""

        pass

    def get_app_path(self) -> str:
        """Retrieves application path.

        Returns:
            For a .app / .exe this returns the absolute path to .../slateAI.app/Contents/MacOS.
            For a folder this returns the absolute path to .../slateAI.

            If the application is run as a bundle, the PyInstaller bootloader extends the sys module by a flag
            frozen=True and sets the app path into variable _MEIPASS.
        """

        application_path = ""
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            # FUTURE: Get parent dir (not needed for now):
            # application_path = os.path.abspath(os.path.join(application_path, os.pardir))
        return application_path

    def get_data_path(self) -> str:
        """Returns the path for the Application Support / Local App Data directory.

        If the directory does not exist yet, it will be created.
        """

        data_path = ""
        if _platform == "darwin":
            # MAC OS X
            data_path = "/Library/Application Support"
        else:
            # WINDOWS
            data_path = os.getenv('LOCALAPPDATA')

        data_path += "/slateAI"

        if not os.path.exists(data_path):
            os.makedirs(data_path)

        return data_path