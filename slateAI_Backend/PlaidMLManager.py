"""A class that creates and manages a PlaidML user configuration file.
"""

from __future__ import print_function
import os
import sys
from six.moves import input
import plaidml
import plaidml.exceptions
import plaidml.settings
import tensorflow as tf
from typing import Tuple, List

class PlaidMLManager:
    """Manages the PlaidML user configuration file.

    Attributes:
        devices_normal: List of all non-experimental devices.
        devices_experimental: List of all experimental devices.
        devices_normal_working: List of all non-experimental working devices.
        devices_experimental_working: List of all experimental working devices.
        device_active_name: Name of the currently active device.
        device_active_experimental: Bool indicating whether device_active_name is experimental.
        standard_tf_device: Standard Tensorflow device in case PlaidML is not viable.
    """

    def __init__(self):
        """Initializes the PlaidMLManager and all class attributes."""

        self.devices_normal, self.devices_experimental = self.get_devices()
        self.devices_normal_working, self.devices_experimental_working = self.get_working_devices()

        if not self.is_setup_done():
            if len(self.devices_experimental_working) > 0:
                self.device_active_name = self.devices_experimental_working[-1]
                self.device_active_experimental = True
                self.set_device(self.device_active_name, experimental=self.device_active_experimental)
            elif len(self.devices_normal_working) > 0:
                self.device_active_name = self.devices_normal[-1]
                self.device_active_experimental = False
                self.set_device(self.device_active_name, experimental=self.device_active_experimental)
            else:
                print("ERROR NO PLAIDML DEVICE WORKING")
        else:
            self.device_active_name = plaidml.settings.device_ids[0]
            self.device_active_experimental = plaidml.settings.experimental

        self.standard_tf_device = 'gpu:0' if tf.test.is_gpu_available() else 'cpu'

    def get_devices(self) -> Tuple[List]:
        """Returns all PlaidML devices available on the system."""

        ctx = plaidml.Context()
        plaidml.quiet()
        devices_normal = []
        devices_experimental = []

        # Set settings as if nothing is configured so every possible device is returned:
        plaidml.settings._setup_for_test(plaidml.settings.user_settings)

        # Get normal devices:
        plaidml.settings.experimental = False
        devices, _ = plaidml.devices(ctx, limit=100, return_all=True)
        for device in devices:
            devices_normal.append(device.id.decode())

        # Get experimental devices:
        plaidml.settings.experimental = True
        devices, unmatched = plaidml.devices(ctx, limit=100, return_all=True)
        for device in devices:
            devices_experimental.append(device.id.decode())

        # Reset to system configuration:
        plaidml.settings._load()
        plaidml.settings._setup = False

        return devices_normal, devices_experimental

    def get_working_devices(self) -> Tuple[List]:
        """Tests all available PlaidML devices and returns the working ones.

        Returns:
            Working devices, divided in normal and experimental.
        """

        devices_normal_working = []
        devices_experimental_working = []

        for device in self.devices_normal:
            if self.test_device(device, experimental=False):
                devices_normal_working.append(device)

        for experimental_device in self.devices_experimental:
            if self.test_device(experimental_device, experimental=True):
                devices_experimental_working.append(experimental_device)

        return devices_normal_working, devices_experimental_working

    def is_setup_done(self) -> bool:
        """Checks if PlaidML setup has already been done.

        Returns:
            True if setup already done. Otherwise false.
        """

        settings = plaidml.settings
        if not settings.setup and not settings.session:
            print("plaidml setup NOT done")
            return False
        else:
            print("plaidml setup done")
            print("active Device: ", plaidml.settings.device_ids[0])
            print("experimental_mode:", plaidml.settings.experimental)
            return True

    def set_device(self, device: str, experimental: bool = True):
        """Sets device from params as PlaidML inference device, if it passes the test_device test."""

        if self.test_device(device, experimental):
            ctx = plaidml.Context()
            plaidml.quiet()
            if experimental:
                plaidml.settings.experimental = True
            else:
                plaidml.settings.experimental = False
            plaidml.settings.device_ids = [device]
            print("\nSelected device:\n    {0}".format(plaidml.devices(ctx)[0]))
            plaidml.settings.save(plaidml.settings.user_settings)
        else:
            print("Device cannot be set, since it doesn't pass the test.")

    def test_device(self, device, experimental = True) -> bool:
        """Tests device from params with a matrix operation. Intel HD is omitted due to Windows not working with it.

        Returns:
            True if device works. Otherwise false.
        """

        # Save system settings
        preset_experimental = plaidml.settings.experimental
        preset_device_ids = plaidml.settings.device_ids

        if "intel_hd" in device:
            print("Intel HD currently not supported")
            return False
        try:
            ctx = plaidml.Context()
            plaidml.quiet()
            if experimental:
                plaidml.settings.experimental = True
            else:
                plaidml.settings.experimental = False
            print("test_device: ", device)
            print("experimental: ", plaidml.settings.experimental)
            plaidml.settings.device_ids = [device]

            with plaidml.open_first_device(ctx) as dev:
                matmul = plaidml.Function(
                    "function (B[X,Z], C[Z,Y]) -> (A) { A[x,y : X,Y] = +(B[x,z] * C[z,y]); }")
                shape = plaidml.Shape(ctx, plaidml.DType.FLOAT32, 3, 3)
                a = plaidml.Tensor(dev, shape)
                b = plaidml.Tensor(dev, shape)
                c = plaidml.Tensor(dev, shape)
                plaidml.run(ctx, matmul, inputs={"B": b, "C": c}, outputs={"A": a})

            print("Whew. That worked.\n")

            #reset system settings
            plaidml.settings.experimental = preset_experimental
            plaidml.settings.device_ids = preset_device_ids
            return True
        except:
            plaidml.settings.experimental = preset_experimental
            plaidml.settings.device_ids = preset_device_ids
            return False



    def main(self):
        """Default PlaidML setup function. Deprecated, do not call."""
        ctx = plaidml.Context()
        plaidml.quiet()

        def choice_prompt(question, choices, default):
            inp = ""
            while not inp in choices:
                inp = input("{0}? ({1})[{2}]:".format(question, ",".join(choices), default))
                if not inp:
                    inp = default
                elif inp not in choices:
                    print("Invalid choice: {}".format(inp))
            return inp

        print("""PlaidML Setup ({0})
                
                Thanks for using PlaidML!
                
                The feedback we have received from our users indicates an ever-increasing need
                for performance, programmability, and portability. During the past few months,
                we have been restructuring PlaidML to address those needs.  To make all the
                changes we need to make while supporting our current user base, all development
                of PlaidML has moved to a branch — plaidml-v1. We will continue to maintain and
                support the master branch of PlaidML and the stable 0.7.0 release.
                
                Read more here: https://github.com/plaidml/plaidml 
                
                Some Notes:
                  * Bugs and other issues: https://github.com/plaidml/plaidml/issues
                  * Questions: https://stackoverflow.com/questions/tagged/plaidml
                  * Say hello: https://groups.google.com/forum/#!forum/plaidml-dev
                  * PlaidML is licensed under the Apache License 2.0""".format(plaidml.__version__))

        # Placeholder env var
        if os.getenv("PLAIDML_VERBOSE"):
            # change verbose settings to PLAIDML_VERBOSE, or 4 if PLAIDML_VERBOSE is invalid
            try:
                arg_verbose = int(os.getenv("PLAIDML_VERBOSE"))
            except ValueError:
                arg_verbose = 4
            plaidml._internal_set_vlog(arg_verbose)
            print("INFO:Verbose logging has been enabled - verbose level", arg_verbose, "\n")
            if plaidml.settings.default_config:
                (cfg_path, cfg_file) = os.path.split(plaidml.settings.default_config)
            else:
                (cfg_path, cfg_file) = ("Unknown", "Unknown")
            if plaidml.settings.experimental_config:
                (exp_path, exp_file) = os.path.split(plaidml.settings.experimental_config)
            else:
                (exp_path, exp_file) = ("Unknown", "Unknown")

        # Operate as if nothing is set
        plaidml.settings._setup_for_test(plaidml.settings.user_settings)

        plaidml.settings.experimental = False
        devices, _ = plaidml.devices(ctx, limit=100, return_all=True)
        plaidml.settings.experimental = True
        exp_devices, unmatched = plaidml.devices(ctx, limit=100, return_all=True)

        if not (devices or exp_devices):
            if not unmatched:
                print("""No OpenCL devices found. Check driver installation.
                        Read the helpful, easy driver installation instructions from our README:
                        http://github.com/plaidml/plaidml""")
            else:
                print("""No supported devices found. Run 'clinfo' and file an issue containing the full output.""")
            sys.exit(-1)

        if devices and os.getenv("PLAIDML_VERBOSE"):
            print("Default Config File Location:")
            print("   {0}/".format(cfg_path))

        print("\nDefault Config Devices:")
        if not devices:
            print("   No devices.")
        for dev in devices:
            print("   {0} : {1}".format(dev.id.decode(), dev.description.decode()))

        if exp_devices and os.getenv("PLAIDML_VERBOSE"):
            print("\nExperimental Config File Location:")
            print("   {0}/".format(exp_path))

        print("\nExperimental Config Devices:")
        if not exp_devices:
            print("   No devices.")
        for dev in exp_devices:
            print("   {0} : {1}".format(dev.id.decode(), dev.description.decode()))

        print(
            "\nUsing experimental devices can cause poor performance, crashes, and other nastiness.\n")
        exp = "y" #choice_prompt("Enable experimental device support", ["y", "n"], "n")
        plaidml.settings.experimental = exp == "y"
        try:
            devices = plaidml.devices(ctx, limit=100)
        except plaidml.exceptions.PlaidMLError:
            print("\nNo devices available in chosen config. Rerun plaidml-setup.")
            sys.exit(-1)

        if devices:
            dev = 1
            if len(devices) > 1:
                print("""Multiple devices detected (You can override by setting PLAIDML_DEVICE_IDS).
                Please choose a default device:""")
                devrange = range(1, len(devices) + 1)
                for i in devrange:
                    print("   {0} : {1}".format(i, devices[i - 1].id.decode()))
                #todo: make user choose device via gui/extensions, take last device for now,
                # so its at least not th stadard cpu if available
                dev = len(devices)#choice_prompt("\nDefault device", [str(i) for i in devrange], "1")
            plaidml.settings.device_ids = [devices[int(dev) - 1].id.decode()]

        print("\nSelected device:\n    {0}".format(plaidml.devices(ctx)[0]))

        print("\nAlmost done. Multiplying some matrices...")
        # Reinitialize to send_message_to_clients a usage report
        print("Tile code:")
        print("  function (B[X,Z], C[Z,Y]) -> (A) { A[x,y : X,Y] = +(B[x,z] * C[z,y]); }")
        with plaidml.open_first_device(ctx) as dev:
            matmul = plaidml.Function(
                "function (B[X,Z], C[Z,Y]) -> (A) { A[x,y : X,Y] = +(B[x,z] * C[z,y]); }")
            shape = plaidml.Shape(ctx, plaidml.DType.FLOAT32, 3, 3)
            a = plaidml.Tensor(dev, shape)
            b = plaidml.Tensor(dev, shape)
            c = plaidml.Tensor(dev, shape)
            plaidml.run(ctx, matmul, inputs={"B": b, "C": c}, outputs={"A": a})
        print("Whew. That worked.\n")

        sav = "y"#choice_prompt("Save settings to {0}".format(plaidml.settings.user_settings), ["y", "n"],"y")
        if sav == "y":
            plaidml.settings.save(plaidml.settings.user_settings)
    print("Success!\n")


if __name__ == "__main__":
    PlaidMLManager().main()
