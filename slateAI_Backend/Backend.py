"""Starting point of the Endslate.AI Backend.

The Endslate.AI Backend communicates with the Endslate.AI Extensions
and runs inference on media files.
"""


import os
os.environ["KERAS_BACKEND"] = "plaidml.keras.backend"  # KERAS_BACKEND needs to be set before Keras is imported!

import plaidml.settings
from keras.models import load_model
from keras.preprocessing import image
import concurrent.futures
import time
import datetime
import tensorflow as tf
import numpy as np
import asyncio
import json
import websockets
import collections
import psutil
import itertools
import sys
from sys import platform as _platform
from sys import exit
import imageio_ffmpeg
from videoprops import get_video_properties
import mimetypes

from PathManager import PathManager
from LicenseManager import LicenseManager
from PortManager import PortManager
from ConfigManager import ConfigManager
from LogManager import LogManager
from PlaidMLManager import PlaidMLManager
from AudioAnalyzer.AudioAnalyzer import AudioAnalyzer
from VideoAnalyzer.VideoAnalyzer import VideoAnalyzer
from VideoAnalyzer.Yolo3Model import Yolo3Model

# GUI
from PySide2.QtWidgets import (QApplication, QProgressBar, QWidget)
from UserInterface.logic_main_window import MainWindow
from asyncqt import QEventLoop, QThreadExecutor
import PyQt5
# os.environ["QT_API"] = "pyside2" - wenn pyside2 15.5.1 relased ist kommt der pyqt5 import weg

# Hidden imports for PyInstaller: Keras / PlaidML
import keras
import plaidml.keras.backend
import plaidml.keras
import plaidml
import plaidml.exceptions
import plaidml.settings

# Hidden imports for PyInstaller: Librosa
import sklearn.utils._cython_blas
import sklearn.neighbors.typedefs
import sklearn.neighbors.quad_tree
import sklearn.tree._utils
import scipy._lib.messagestream
import sklearn.tree


def exit_if_already_running():
    """Exits the program if another instance of the backend is already running."""

    if _platform == "darwin":  # macOS
        stream = os.popen('ps -fA | grep slateAI')
        output = stream.readlines()
        number_of_instances_running = 0
        for line in output:
            words = line.split(" ")
            if "slateAI" in words[-1] and not "grep" in words[-2] and not "sudo" in words[-3]:
                number_of_instances_running += 1
        if number_of_instances_running > 1:
            print('already running. exiting!')
            exit(1)

    else:  # Windows
        from win32event import CreateMutex
        from win32api import GetLastError
        from winerror import ERROR_ALREADY_EXISTS

        handle = CreateMutex(None, 1, 'slateaibackend')

        if GetLastError() == ERROR_ALREADY_EXISTS:
            print('already running. exiting!')
            exit(1)


########################################################################################################################
# EXTENSION COMMUNICATION FUNCTIONS
########################################################################################################################

async def register_client(websocket: websockets.server.WebSocketServerProtocol):
    """Adds a websocket client to the list of clients.

    Args:
        websocket: The websocket object of the client.
    """

    global clients
    clients.add(websocket)
    print("A client on port ", websocket.port, " connected")
    print("clients", clients)


def unregister_disconnected_clients():
    """Removes websocket clients that are not responding from the list of clients."""

    global clients
    clients_new = set()

    for client in clients:
        if str(client.state) != 'State.CLOSED':
            clients_new.add(client)
        else:
            print("A User on port ", client.port, " disconnected")
            print("clients", clients)

    clients = clients_new


async def send_message_to_clients(message: str):
    """Sends a message to every client.

    Args:
        message: The message to be sent to all clients.
    """

    for client in clients:
        await client.send(message)

    print("##### Message sent to clients: #####")
    print(message, "\n")


async def send_possible_devices():
    """Sends possible PlaidML devices to all clients."""

    possible_devices = {'possibleDevices': {'devices': plaidml_manager.devices_normal,
                                           'experimentalDevices': plaidml_manager.devices_experimental_working}}
    possible_devices = json.dumps(possible_devices)
    await send_message_to_clients(possible_devices)


async def send_active_device(device: str, experimental: bool = True):
    """Sends the currently active PlaidML device to all clients.

    Args:
        device: The device to be sent to clients as the currently active device.
        experimental: True if device is experimental. Otherwise false.
    """

    if experimental:
        device += " (experimental)"
    device = {'chosenDevice': device}
    device = json.dumps(device)
    await send_message_to_clients(device)


async def send_status():
    """Sends current status to all clients.

    Status contains the total amount of tasks, the remaining amount, the task that in progress and the device used.
    """

    global task_current
    global task_queue
    global task_total
    task_remaining = len(task_queue) if task_current == '' else len(task_queue) + 1

    status_dict = {'Statusinfo': {'totalItems': task_total,
                                  'itemsRemaining': task_remaining,
                                  'current': task_current,
                                  'activeDevice': plaidml_manager.device_active_name,
                                  'experimental': plaidml_manager.device_active_experimental}}
    status_string = json.dumps(status_dict)
    await send_message_to_clients(status_string)


async def send_status_loop():
    """Sends current status to all clients, once every second."""

    while True:
        try:
            await asyncio.sleep(1)
            await send_status()
        except:
            print("send_status_loop FAILED")


async def receive_messages(websocket, port):
    """Listens for messages on the socket/port from params and triggers actions accordingly.

    This is the place where pausing/resuming, device management and task_queue population happen.

    Args:
        websocket: The websocket to listen for messages on.
        port: The port to listen for messages on.
    """

    global paused
    global task_total
    global task_queue

    try:
        await register_client(websocket)
        async for message in websocket:
            print("##### Message received: #####")
            print(message, "\n")

            if message == "undefined" or message == "":
                pass

            elif message == "ping":
                await websocket.send("slateai alive on Port " + str(port))

            elif message == "PAUSE":
                paused = True

            elif message == "RESUME":
                paused = False

            elif message == "GETDEVICES":
                await send_possible_devices()

            elif "SETDEVICE" in message:
                plaidml_manager.device_active_name = message.split(":")[-1].split(" (experimental)")[0]
                experimental = True if " (experimental)" in message else False
                plaidml_manager.set_device(plaidml_manager.device_active_name, experimental)
                await send_active_device(plaidml_manager.device_active_name, experimental)

            else:  # Message has to be one or more Paths for files, which have to be analyzed
                paths = message.split(",")
                for path in paths:
                    task_total += 1
                    task_queue.appendleft(path)
            await send_status()

    except websockets.exceptions.ConnectionClosedError:
        print("websocket connection closed")


########################################################################################################################
# File ANALYSIS FUNCTIONS
########################################################################################################################

def analyze_file(path: str) -> str:
    """The file is analyzed according to its mimetype.

    Each audio file is passed on to the AudioAnalyzer.
    For each video file a VideoAnalyzer is created.

    Args:
        path: The path to the file that needs to be analyzed.

    Returns:
        A dict representing the sync points for the file: {path: [420.69, 123.45]}
    """

    mimetype = mimetypes.guess_type(path)[0].split('/')[0]

    if mimetype == 'video':
        window.console("Analyzing Video: " + path)
        video_analyzer = VideoAnalyzer(video_path=path,
                                       model=yolo_v3_model,
                                       sample_rate=30,
                                       confidence_threshold=0.85,
                                       logger=logger,
                                       plaidml_manager=plaidml_manager)
        syncpoints, fps, sample_rate, resolution, file_duration = video_analyzer.analyze_video(workers=4,
                                                                                               max_steps=15,
                                                                                               max_retries=2)
        return {path: syncpoints}

    elif mimetype == 'audio':
        window.console("Analyzing Audio: " + path)
        syncpoints = audio_analyzer.analyze(path)
        return {path: syncpoints}

    else:
        return {path: []}


async def analyze_queue_loop():
    """Periodically looks into task_queue and manages analysis jobs.

    Runs once a second.
    Removes disconnected clients.
    Checks if there is a path to process in the task_queue.
    If there is, an appropriate analysis job is created and the queue is updated.
    """

    global task_current
    global paused
    global task_queue
    global task_total

    while True:

        try:
            unregister_disconnected_clients()
            await asyncio.sleep(1)

            if len(task_queue) > 0 and not paused:
                path = task_queue.pop()
                task_current = path.split('/')[-1].split('\\')[-1]

                print("Current Task: ", task_current)
                window.console("Currently working on " + path)

                syncpoints = await loop.run_in_executor(None, analyze_file, path)
                syncpoints = json.dumps(syncpoints)
                await send_message_to_clients(syncpoints)

                if len(task_queue) == 0:
                    task_current = ""
                    await send_status()
                    await send_message_to_clients("Done")
                    window.console("Waiting for Input")
                    task_total = 0

        except Exception as e:
            print("analyze_queue_loop() failed")
            print(e.message)


########################################################################################################################
# STARTING POINT
########################################################################################################################

if __name__ == '__main__':

    ###############################################################################
    # Start backend
    ###############################################################################

    exit_if_already_running()

    path_manager = PathManager()
    config = ConfigManager()

    logger = LogManager()
    logger.log("Backend started", "Start")

    license = LicenseManager()
    if not license.check_valid():
        sys.exit("License expired")

    ###############################################################################
    # Audio & Video Analyzer
    ###############################################################################

    plaidml_manager = PlaidMLManager()
    audio_analyzer = AudioAnalyzer(logger, plaidml_manager)
    pb_filepath = os.path.join(path_manager.get_app_path(), 'yolov3_slates.pb')
    yolo_v3_model = Yolo3Model(pb_filepath)

    ###############################################################################
    # Global Variables
    ###############################################################################

    task_queue = collections.deque()
    task_total = 0
    task_current = ""
    paused = False
    clients = set()

    ###############################################################################
    # Port handling
    ###############################################################################

    port_manager = PortManager(config)
    if len(sys.argv) > 1 and "port" in sys.argv[1]:
        port_manager.port = int(sys.argv[1].split('=')[1])
        print("using ", port_manager.port, " given as parameter")
    port = port_manager.get_port()

    ###############################################################################
    # GUI
    ###############################################################################

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()
    window.console("test")
    app.exec_

    ###############################################################################
    # AsyncIO co-routines
    ###############################################################################

    asyncio.get_event_loop().create_task(analyze_queue_loop())

    asyncio.get_event_loop().create_task(send_status_loop())

    start_server = websockets.serve(receive_messages, "localhost", port)
    asyncio.get_event_loop().run_until_complete(start_server)

    asyncio.get_event_loop().run_forever()