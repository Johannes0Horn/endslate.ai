"""A class for multi-threading jump search tasks.
"""

import threading
import time
from typing import Tuple, Dict


class SearchThread(threading.Thread):
    """This class overrides the functionality of a normal thread with a jump search task.

    The function for the jump search itself lies in VideoAnalyzer and is referenced through the video_analyzer param.
    Usage inside VideoAnalyzer:
    worker = SearchThread(0, (0,100), {}, self, 0)
    worker.start()
    -> The "self" is the important part here. The other attributes are passed on to video_analyzer.jump_search().

    Attributes:
        thread_id: A unique number identifying the thread.
        chunk: A tuple containing the start and end frame numbers of the chunk to be analyzed by the thread.
        predictions: A dict containing the predicted confidences for each analyzed frame: {frame_number: confidence,...}
        video_analyzer: The VideoAnalyzer object of the file in question.
        steps_done: Amount of frames analyzed. Starts at 0, ends at video_analyzer.sample_rate.
        start = Timestamp, when the thread has been started running.
        end = Timestamp, when the thread has finished running.
    """

    def __init__(self, thread_id: int, chunk: Tuple[int, int], predictions: Dict[int, float],
                 video_analyzer, steps_done: int):
        """Initializes the thread and most of its attributes.

        Args:
            thread_id: A unique number identifying the thread.
            chunk: A tuple containing the start and end frame numbers of the chunk to be analyzed by the thread.
            predictions: A dict containing the predicted confidences for each analyzed frame:
                {frame_number: confidence, ...}
            video_analyzer: The VideoAnalyzer object of the file in question.
                (No type hinting because of errors due to recursive class imports).
            steps_done: Amount of frames analyzed. Starts at 0, ends at video_analyzer.sample_rate.
        """

        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.chunk = chunk
        self.predictions = predictions
        self.video_analyzer = video_analyzer
        self.steps_done = steps_done

    def terminate(self):
        """Terminates the thread."""
        self._running = False

    def run(self):
        """Performs jump search within the defined chunk.

        The jump_search() function of the VideoAnalyzer is called and timed.
        Do not call separately. The thread starts by calling worker.start().
        """

        self.start = time.time()
        print("Starting SearchThread {}".format(self.thread_id))
        self.video_analyzer.jump_search(self.chunk, self.thread_id, self.predictions, self.steps_done)
        print("Thread {} Done".format(self.thread_id))
        self.end = time.time()