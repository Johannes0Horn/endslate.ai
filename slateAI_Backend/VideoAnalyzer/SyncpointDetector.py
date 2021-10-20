"""A class containing functions for efficient slate sync point detection in groups of consecutive video frames.
"""

import cv2
import numpy as np
from VideoAnalyzer.config import CLASS_INDEX_DICT
from VideoAnalyzer.Yolo3Model import Yolo3Model
from typing import List, Tuple, Dict, Any, Union


class SyncpointDetector:
    """For each group of consecutive slate-containing frames the exact sync points (slate is closed) are found.

    Attributes:
        confidence_margin:
        confidence_threshold: Minimal confidence needed to categorize an image as having an open/closed slate in it.
        model: The machine learning model used for inference.
        cap: An OpenCV VideoCapture object for the file.
        sample_rate: The step size used by the VideoAnalyzer while looking for slates in frames.
            Every (sample_rate)th frame was analyzed. Used here to extend/pad the borders of a "slate group"
            by one sample in each direction.
    """

    def __init__(self, confidence_margin: int, confidence_threshold: float,
                 model: Yolo3Model, cap: cv2.VideoCapture, sample_rate: int):
        """Initializes the SyncPointDetector and its class attributes."""

        self.confidence_margin = confidence_margin
        self.confidence_threshold = confidence_threshold
        self.model = model
        self.cap = cap
        self.sample_rate = sample_rate

    def find_all_syncpoints_binary(self, groups: List[List[int]],
                                   max_steps: int = 20, max_retries: int = 3) -> List[int]:
        """For each group of consecutive slate-containing frames the exact sync points (slate is closed) are found.

        Each group is searched in a binary manner until a sync point can be found, using syncpoint_search_fast.

        Args:
            groups: A list of lists/groups to look for sync points in.
            max_steps: Maximal amount of recursive steps the binary search will make while searching in a slate group.
            max_retries: Maximal amount of times a slate group will be searched for sync points.

        Returns:
            A list of found slate sync points, each as frame numbers.
        """

        syncpoints = list()

        for group in groups:
            first_frame = group[0]
            last_frame = group[-1]

            syncpoint = self.syncpoint_search_fast(first_frame, last_frame, max_steps, max_retries)
            syncpoints.append(syncpoint)

            print("Syncpoint = {}".format(syncpoint))
            print("-" * 100)

        return syncpoints

    def syncpoint_search_fast(self, first_frame_number: int, last_frame_number: int,
                              max_steps: int = 20, max_retries: int = 3) -> int:
        """The slate group defined by first_frame_number and last_frame_number is widened and sent to the binary search.

        The frame group borders are extended bs sample_rate in each direction.
        Example: With a sample_rate of 30 a group defined by frames 69 and 420 grows to include frames 39 - 450.
        This is the initial starting point of the binary search algorithm. The 1st frame to analyze is determined here.

        Args:
            first_frame_number: Index of the first frame of the group to analyze.
            last_frame_number: Index of the last frame of the group to analyze.
            max_steps: Maximal amount of recursive steps the binary search will make while searching in a slate group.
            max_retries: Maximal amount of times a slate group will be searched for sync points.

        Returns:
            The sync point found within the group.
        """

        total_number_of_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        first_frame_number -= self.sample_rate
        first_frame_number = 0 if first_frame_number < 0 else first_frame_number

        last_frame_number += self.sample_rate
        last_frame_number = total_number_of_frames if last_frame_number > total_number_of_frames \
            else total_number_of_frames

        print("Searching frames {} - {}".format(first_frame_number, last_frame_number))

        step_size = (last_frame_number - first_frame_number) // 2
        frame_number = last_frame_number - step_size

        return self.syncpoint_binary_search(first_frame_number, last_frame_number, frame_number,
                                            step_size, step_size, max_steps, max_retries)

    def syncpoint_binary_search(self, first_frame: int, last_frame: int, frame_number: int, step_size: int,
                                original_step_size: int, max_steps: int, max_retries: int) -> int:
        """Recursively searches for the frame where the slate is closed in a binary manner.

        Args:
            first_frame: Index of the first frame of the group.
            last_frame: Index of the last frame of group.
            frame_number: Index of the frame in the middle, the one that will be analyzed in this iteration.
            step_size: Indicates how many frames lie in between the last analysed frame and this one.
            max_steps: Amount of recursive steps left before the binary search auto-finishes.
            max_retries: Maximal amount of times the group will be searched.
        """

        print("Frame = {}".format(frame_number))
        print("Step Size = {}".format(step_size))

        if max_steps == 0:
            return

        if step_size == 1:
            max_steps -= 1

        predictions = self.make_predictions(frame_number)
        class_indexes = self.get_class_indexes(predictions)

        if len(class_indexes) == 0:
            class_indexes = self.fill_empty_predictions(first_frame, last_frame, frame_number)

        print("Classes detected = {}".format(class_indexes))

        if np.mean(class_indexes) == 1.:  # step forth when all three frames are open
            new_step_size = np.ceil(step_size / 2)
            new_frame_number = frame_number + new_step_size

            return self.syncpoint_binary_search(first_frame, last_frame, new_frame_number,
                                                new_step_size, original_step_size, max_steps, max_retries)

        elif np.mean(class_indexes) == 0.:  # step back when all three frames are closed
            new_step_size = np.ceil(step_size / 2)
            new_frame_number = frame_number - new_step_size

            return self.syncpoint_binary_search(first_frame, last_frame, new_frame_number,
                                                new_step_size, original_step_size, max_steps, max_retries)

        else:
            padded_indexes = self.pad_final_prediction(frame_number=frame_number)
            syncpoint = self.improved_syncpoint_detection(padded_indexes[:, 0],
                                                          padded_indexes[:, 1],
                                                          padded_indexes[:, 2])

            if syncpoint != None:
                return syncpoint
            else:
                if max_retries == 0:
                    print("Max. retries reached. Returning most likely sync point")
                    return self.return_syncpoint_on_timeout(frame_number, np.array(class_indexes))

                print("Candidate unlikely to be correct. Restarting search from random frame.")
                new_frame_number = np.random.randint(first_frame, last_frame)
                return self.syncpoint_binary_search(first_frame, last_frame, new_frame_number, original_step_size,
                                               original_step_size, max_steps, max_retries - 1)

    def make_predictions(self, frame_number: int) -> Tuple[Dict[str, Union[int, np.ndarray]],
                                                           Dict[str, Union[int, np.ndarray]],
                                                           Dict[str, Union[int, np.ndarray]]]:
        """Uses the machine learning model to predict the open/closed state of the slate in a frame and its neighbors.

        Args:
            frame_number: The frame in question.

        Returns:
            A tuple with predictions for the frame in question and its two direct neighbors.
        """

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        _, image = self.cap.read()

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
        _, prev_image = self.cap.read()

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number + 1)
        _, next_image = self.cap.read()

        current_prediction = {'frame_number': frame_number, 'pred': np.array(self.model.predict(image))}
        previous_prediction = {'frame_number': frame_number - 1, 'pred': np.array(self.model.predict(prev_image))}
        next_prediction = {'frame_number': frame_number + 1, 'pred': np.array(self.model.predict(next_image))}

        return previous_prediction, current_prediction, next_prediction

    @staticmethod
    def get_class_indexes(predictions: Tuple[Dict[str, Union[int, np.ndarray]], ...]) -> List:
        """Given a tuple of predictions (coming from make_predictions), the predicted classes are extracted.

        Args:
            predictions: The predictions to extract the class indices from.

        Returns:
            A list of the predicted class indices.
        """

        indices = list()
        for pred in predictions:
            if len(pred['pred']) > 0:
                indices.append(int(pred['pred'][0][-1]))
        return indices

    def fill_empty_predictions(self, first_frame: int, last_frame: int, current_frame: int) -> List[int]:
        """Depending on the position of the current_frame within the group boundaries, 3 class indices are returned.

        Args:
            first_frame: Index of the first frame of the group.
            last_frame: Index of the last frame of the group.
            current_frame: Index of the frame in question.

        Returns:
            A list of three class indices, either all "open" or all "closed".
        """

        open_idx = CLASS_INDEX_DICT['open']
        closed_idx = CLASS_INDEX_DICT['closed']

        if abs(last_frame - current_frame) < abs(first_frame - current_frame):
            return [closed_idx, closed_idx, closed_idx]
        else:
            return [open_idx, open_idx, open_idx]

    def pad_final_prediction(self, frame_number: int) -> np.ndarray:
        """(1 x confidence_margin) frames before and after the frame from param are infered again.

        Args:
            frame_number: The frame in question.

        Returns:
            An array containing the predictions for the ((2 x confidence_margin) + 1) frames:
            np.ndarray[np.ndarray[frame_index, class_index, confidence], ...]
        """

        padded_prediction = list()

        # backward padding
        j = frame_number - self.confidence_margin - 1
        for i in range(self.confidence_margin):
            current_frame = j + i + 1
            print("Padding frame = {}".format(current_frame))
            self.pad(current_frame, padded_prediction)

        # forward padding
        j = frame_number
        for i in range(self.confidence_margin + 1):
            current_frame = j + i
            print("Padding frame = {}".format(current_frame))
            self.pad(current_frame, padded_prediction)

        return np.array(padded_prediction)

    def pad(self, current_frame: int, padded_prediction: List):
        """Inferes the current_frame and writes prediction into padded_prediction variable.

        One prediction has the following form: np.ndarray[frame_index, class_index, confidence].

        Args:
            current_frame: The frame to infere.
            padded_prediction: The list of predictions to add the current prediction to.
        """

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        _, image = self.cap.read()
        prediction = self.model.predict(image)
        class_idx = prediction[0][-1]
        conf = prediction[0][-2]
        padded_prediction.append(np.array([current_frame, class_idx, conf]))

    def improved_syncpoint_detection(self, frames: np.ndarray, predicted_states: np.ndarray,
                                     confidence_values: np.ndarray) -> int:
        """Uses the predicted classes and confidences to guess the likeliest sync point frame index.

        Args:
            frames: A list of consecutive frame indices.
            predicted_states: The predicted class indices of the frame indices in the frame param.
            confidence_values: The confidence values of the predicted classes of the frame indices in the frame param.

        Returns:
            The frame index of the retrieved sync point.
        """

        detected_syncpoints = self.find_sync_points(predicted_states)
        confidence_values[np.where(confidence_values == None)] = 0.5

        for p in detected_syncpoints:
            avg_conf = np.mean(confidence_values)
            print("Syncpoint candidate found!")
            print("Average Detection Confidence = {}".format(avg_conf))

            if avg_conf >= self.confidence_threshold:
                return int(frames[p])

    def find_sync_points(self, states: np.ndarray) -> List[int]:
        """Searches for the first closed frames after an open frame -> sync point candidates.

        Args:
            states: An array of class indices: np.ndarray[1,1,1,0,0,0,0,,1,1,1].

        Returns:
            A list of sync point candidates.
        """

        syncpoints = list()
        gt_1 = np.array(states).astype(np.float32).astype(np.int32)

        for i in range(len(gt_1) - 1):
            state_0 = gt_1[i]
            state_1 = gt_1[i + 1]

            if state_0 == 1 and state_1 == 0:
                syncpoints.append(i)

        return syncpoints

    @staticmethod
    def return_syncpoint_on_timeout(frame_number: int, class_indexes: np.ndarray) -> int:
        """Extracts the first possible sync point within an array of predicted class indices. This is a last resort!

        Args:
            frame_number: The frame index the binary search is currently at.
            class_indexes: An array of predicted class indices.
        """
        sync_index = np.where(class_indexes == 0)[0][0]
        return frame_number - (sync_index - 1)
