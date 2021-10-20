"""A class that handles license verification.
"""

import time
import os
import os.path
from PathManager import PathManager
from CryptoManager import CryptoManager
from typing import Any

class LicenseManager:
    """License validation management.

    Usage: LicenseManager().check_license() -> Should return true

    Attributes:
        filepath: Path to the license file.
        crypto_manager: A CryptoManager instance.
        system_time: Time in seconds at the point of class instance creation.
    """

    def __init__(self):
        """Initializes LicenseManager and its class attributes."""

        self.filepath = PathManager().get_data_path() + "/licensefile"
        self.crypto_manager = CryptoManager()
        self.system_time = time.mktime(time.gmtime())

    def write_timestamp_to_file(self, timestamp: Any):
        """Writes timestamp from params into license file."""

        self.crypto_manager.write_encrypted_string_to_file(self.filepath, str(timestamp))

    def write_invalid_license_file(self):
        """Marks license as invalid in the license file."""

        self.crypto_manager.write_encrypted_string_to_file(self.filepath, str("invalid"))

    def get_timestamp_from_file(self):
        """Returns timestamp saved in license file."""

        return self.crypto_manager.get_encrypted_string_from_file(self.filepath)

    def compare_time_with_systemtime(self, timestamp: Any):
        """Returns true if there is a time difference between the system time and the timestamp param.

        Args:
            timestamp: The timestamp that needs to be compared to the system time.
        """

        if float(self.system_time) - float(timestamp) > 0:
            return True
        else:
            return False

    def check_valid(self):
        """Systematically validates license file.

        If the license file does not yet exist, it will be created.
        If the license or system time has been tampered with, the license is marked as invalid.

        Returns:
            True if license is valid. Otherwise false.
        """

        if os.path.isfile(self.filepath) is False:  # License file does not exist
            self.write_timestamp_to_file(self.system_time)
            print("license did not exist... now has been created for the first time")
            return True

        else:
            saved_timestamp = self.get_timestamp_from_file()

            if (saved_timestamp is False):  # System time has been tampered with.
                self.write_invalid_license_file()
                return False

            if "invalid" in saved_timestamp:  # License file has been tampered with.
                return False

            if len(saved_timestamp.split()) is 1:  # App has been opened only once before.
                if self.compare_time_with_systemtime(saved_timestamp):
                    new_timestamps = saved_timestamp + " " + str(self.system_time)
                    self.write_timestamp_to_file(new_timestamps)
                    return True
                else:  # System time has been tampered with.
                    return False

            if len(saved_timestamp.split()) is 2:  # App has been opened at leased two times.
                timestamp_app_first_opened, timestamp_app_last_opened = saved_timestamp.split()
                if self.compare_time_with_systemtime(timestamp_app_first_opened):
                    if self.compare_time_with_systemtime(timestamp_app_last_opened):
                        new_timestamps = timestamp_app_first_opened + " " + str(self.system_time)
                        self.write_timestamp_to_file(new_timestamps)
                        return True
                    else:
                        self.write_invalid_license_file()
                        return False
                else:
                    self.write_invalid_license_file()
                    return False