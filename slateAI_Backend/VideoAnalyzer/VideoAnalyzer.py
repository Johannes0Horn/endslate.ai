"""A class that is the starting point of the VideoAnalyzer module.
Contains functions for multi-threaded sync point searching inside a video file.
"""

import cv2
import numpy as np
import time
import fleep
from videoprops import get_video_properties
from VideoAnalyzer.SearchThread import SearchThread
from VideoAnalyzer.SyncpointDetector import SyncpointDetector
from VideoAnalyzer.Yolo3Model import Yolo3Model
from LogManager import LogManager
from PlaidMLManager import PlaidMLManager
from typing import List, Tuple, Dict

class VideoAnalyzer:
    """Analyzes one single video file to find clap sync points.

    Creates threads for searching frames with slates inside the video file
    and uses the SyncPointDetector to find exact timestamps where the slate is being closed.

    Attributes:
        cap: An OpenCV VideoCapture object for the file.
        fps: The temporal resolution (frames per second) of the video file.
        resolution: The spacial resoluton [width, height] of the video file.
        frame_count: The total amount of frames in the video file.
        duration: The duration of the video in seconds.
        model: The machine learning model used for inference.
        sample_rate: The step size while looking for slates in frames. Every (sample_rate)th will be analyzed.
        confidence_threshold: Minimal confidence needed to categorize an image as having a slate in it.
        margin: ??? -> Not in need right now.
        video_path: Path of the video file in need of analysis.
        logger: The LogManager to use for logging the analyzed file.
        plaidml_manager = The common PlaidMLManager object.
        start_time = Timestamp of the initialization process / start of analysis.
        syncpoint_detector: The SyncpointDetector object used to find sync points in found slate frames.
    """

    def __init__(self, video_path: str, model: Yolo3Model, sample_rate: int, confidence_threshold: float,
                 logger: LogManager, plaidml_manager: PlaidMLManager, margin: int = 7):
        """Initializes the VideoAnalyzer for a specific video file and all of the class attributes.

        Args:
            video_path: Path of the video file in need of analysis.
            model: The machine learning model used for inference.
            sample_rate: The step size while looking for slates in frames. Every (sample_rate)th will be analyzed.
            confidence_threshold: Minimal confidence needed to categorize an image as having a slate in it.
            logger: The LogManager to use for logging the analyzed file.
            plaidml_manager = The common PlaidMLManager object.
            margin: ??? -> Not in need right now.
        """

        self.cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.resolution = [self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)]
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        self.model = model
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold
        self.margin = margin
        self.video_path = video_path
        self.logger = logger
        self.plaidml_manager = plaidml_manager
        self.start_time = time.time()
        self.syncpoint_detector = SyncpointDetector(confidence_margin=4, confidence_threshold=confidence_threshold,
                                                    model=model, cap=self.cap, sample_rate=sample_rate)

    def analyze_video(self, workers: int, max_steps: int,
                      max_retries: int) -> Tuple[List[float], int, int, List[int], float]:
        """Performs video analysis, looking for slate sync points.

        Creates threads for searching frames with slates inside the video file, creating "slate groups" of
        consecutive slate containing frames. It then uses the SyncPointDetector to find exact timestamps
        where the slate is being closed within the groups. Results are logged.

        Args:
            workers: Amount of threads to use for slate searching.
            max_steps: Maximal amount of recursive steps the SyncPointDetector will make while searching in a group.
            max_retries: Maximal amount of times a slate group will be searched for sync points by SyncPointDetector.

        Returns:
            A list of sync points, the FPS of the video file, the sample_rate / group padding used by the
            SyncPointDetector, the spacial resolution of the video and the duration of the video.
        """

        preds, workers_objects = self.multi_threaded_search(workers)
        slate_frames = np.array(sorted(list(preds.keys())))
        groups = self.group_slate_frames(slate_frames)

        syncpoints_as_frames = self.syncpoint_detector.find_all_syncpoints_binary(groups=groups,
                                                                                  max_steps=max_steps,
                                                                                  max_retries=max_retries)
        syncpoints_as_seconds = [framenumber/self.fps for framenumber in syncpoints_as_frames]

        self.log(syncpoints_as_seconds, time.time()-self.start_time)
        return syncpoints_as_seconds, self.fps, self.sample_rate, self.resolution, self.duration

    def multi_threaded_search(self, workers: int) -> Tuple[Dict[int, float], List[SearchThread]]:
        """Starts multiple threads/workers to search for slates inside frames.

        Divides the video file into chunks of consecutive frames and assigns each chunk to a separate Thread.
        Visual example: a 24 frame video separated into 4 chunks, assigned to 4 workers:
        ###################################################################################################
        ##   |   |   |   |   |   #   |   |   |   |   |   #   |   |   |   |   |   #   |   |   |   |   |   ##
        ##   chunk 0: worker 0   #   chunk 1: worker 1   #   chunk 2: worker 2   #   chunk 3: worker 3   ##
        ##   |   |   |   |   |   #   |   |   |   |   |   #   |   |   |   |   |   #   |   |   |   |   |   ##
        ###################################################################################################
         |___|
         frame
         |_______________________|
                  chunk
        |_________________________________________________________________________________________________|
                                                      file

        Args:
            workers: Amount of chunks and threads/workers.

        Returns:
            A dict with predictions {frame_number: confidence, ...},
            and a list containing all thread objects.
        """

        preds = dict()
        worker_objects = list()
        steps_done = 0

        nb_steps = self.frame_count // self.sample_rate
        print("Total number of steps = {}".format(nb_steps))

        # Create and start threads:
        for i in range(workers):
            lower_border = self.frame_count // workers * i
            upper_border = self.frame_count if i == workers - 1 else self.frame_count // workers * (i + 1)
            chunk = (lower_border, upper_border)

            worker = SearchThread(i, chunk, preds, self, steps_done)
            worker_objects.append(worker)
            worker.start()

        # Wait for threads to finish:
        for worker in worker_objects:
            worker.join()

        return preds, worker_objects

    def jump_search(self, chunk: Tuple[int, int], thread_id: int, predictions: Dict[int, float], steps_done: int):
        """Performs jump search using the sample_rate within a specified chunk of the video file.

        Visual example: chunk = (0, 15). With a sample_rate of 4, every fourth frame of the chunk
        (numbers 0, 4, 8 and 12) is going to be analyzed = infered with the machine learning model.
        #############################################################################################################...
        #-----|     |     |     |-----|     |     |     |-----|     |     |     |-----|     |     |     #-----|     |...
        #--0--|  1  |  2  |  3  |--4--|  5  |  6  |  7  |--8--|  9  | 10  | 11  |-12--| 13  | 14  | 15  #-16--| 17  |...
        #-----|     |     |     |-----|     |     |     |-----|     |     |     |-----|     |     |     #-----|     |...
        #############################################################################################################...
        |_____|_____|
         frame frame ...
        |_______________________________________________________________________________________________|
                                                      chunk
        |____________________________________________________________________________________________________________...
                                                                file ->

        The results of the model predictions are saved into the predictions dict (shared by all workers/threads)
        so that they can be accessed by the thread running the function and the multi_threaded_search function
        that started the threads in the first place.

        Args:
            chunk: A tuple containing the start and end frame numbers of the chunk to be analyzed.
            thread_id: A unique number identifying the thread that is running this function.
            predictions: A dict containing the predicted confidences for each analyzed frame:
                {frame_number: confidence, ...}
            steps_done: Amount of frames analyzed. Starts at 0, ends at video_analyzer.sample_rate.
        """

        cap = cv2.VideoCapture(self.video_path)
        j = 0

        for i in range(chunk[0], chunk[1], self.sample_rate):
            steps_done += 1
            if j % 100 == 0:
                print("Thread {} - frame {}/{}".format(thread_id, i, chunk[1]))
                print("Steps done = {}".format(steps_done))

            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            _, img = cap.read()

            prediction = self.model.predict(img)
            j += self.sample_rate

            if len(prediction) > 0 and prediction[0][4] >= self.confidence_threshold:
                predictions[i] = prediction[0]

    def group_slate_frames(self, frames: List[int]) -> List[List[int]]:
        """A list of frames is grouped by temporal distance.

        A list of frame numbers where slates were found is divided into groups of frames that are close to each other.
        The criterion is two neighboring found frames are at most one sample_rate frames away from each other.
        #
        ##########################################
        Example:
        input = [2, 3, 5, 11, 14, 15, 17, 29, 31]
        sample_rate = 4
        output = [[2,3,5], [11,14,15,17], [29,31]]
        ##########################################
        #
        The groups can be used to search for the exact frame where the slate closes.

        Args:
            frames: A sorted list of frame numbers to sort into groups.

        Returns:
            A list of groups (lists) containing frame numbers, grouped by temporal distance.
        """

        groups = list()

        prev_frame = frames[0]
        current_group = [frames[0]]

        for i, frame in enumerate(frames[1:]):
            diff = frame - prev_frame

            if diff > self.sample_rate or i == (len(frames[1:]) - 1):  # group done
                if len(current_group) > 0:
                    groups.append(current_group)
                current_group = list()
                current_group.append(frame)

            elif diff <= self.sample_rate:  # frame belongs to the current group
                current_group.append(frame)

            prev_frame = frame

        return groups

    def log(self, syncpoints: List[float], inference_duration: float):
        """Logs a successful analysis event using the common logger.

        Args:
            syncpoints: A list of found sync points to log.
            inference_duration: The duration of the inference process to log.
        """

        log_obj = {"file name": self.video_path.split('/')[-1].split('\\')[-1],
                   "file type": str(fleep.get(open(self.video_path,"rb").read(128)).extension),
                   "codec": str(get_video_properties(self.video_path)['codec_name']),
                   "file duration": self.duration,
                   "fps": self.fps,
                   "average frametime": str(self.duration / self.fps),
                   "resolution": self.resolution,
                   "sample rate": self.sample_rate,
                   "framework": "Tensorflow",
                   "device": str(self.plaidml_manager.standard_tf_device),
                   "inference_duration": inference_duration,
                   "results": syncpoints}
        self.logger.log(log_obj, "File Video")
