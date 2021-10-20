"""A class that systematically analyzes audio data looking for clap sync points.
"""


from keras.models import model_from_json
import librosa
import numpy as np
import os
import fleep
import time
from CryptoManager import CryptoManager
from PathManager import PathManager
from PlaidMLManager import PlaidMLManager
from LogManager import LogManager
from typing import List, Tuple, Union


class AudioAnalyzer:
    """A toolset of functions to look for clap sounds in audio data.

    Attributes:
        logger: The logger to use for logging analyzed files.
        plaidml_manager: The PlaidMLManager object needed for accurate logging.
        model: The model used for infering one-second-chunks of audio data.
    """

    def __init__(self, logger: LogManager, plaidml_manager: PlaidMLManager):
        """Initializes the AudioAnalyzer and loads and decrypts the inference model.

        Args:
            logger: The logger to use for logging analyzed files.
            plaidml_manager: The PlaidMLManager object needed for accurate logging.
        """

        self.logger = logger
        self.plaidml_manager = plaidml_manager

        key = b'\xaa\xc0\x82)\x12nc\x92\x03)j\xdf\xc1\xc4\x94\x9d(\x9e[EX\xe8\x15\x23I{\xa2$\x05(\xd2\x11'
        crypto = CryptoManager(key=key)

        path_manager = PathManager()
        path_json = os.path.join(path_manager.get_app_path(), 'AudioAnalyzer/model/model.json.enc')
        path_weights = os.path.join(path_manager.get_app_path(), 'AudioAnalyzer/model/model.h5')

        with open(path_json, 'rb') as json_file:
            crypto_json = json_file.read()
            model_json = crypto.decrypt(crypto_json)
            self.model = model_from_json(model_json)
            self.model.load_weights(path_weights)

    def log(self, path: str, syncpoints: List[float], sr: int, file_duration: float, inference_duration: float):
        """Logs a successful analysis event using the common logger.

        Args:
            path: Path of the analyzed file.
            syncpoints: Timestamps of claps (in seconds) found during analysis.
            sr: Sample rate of the file.
            file_duration: Duration of the file in seconds.
            inference_duration: Duration of inference process in seconds.
        """

        device_name = self.plaidml_manager.device_active_name
        if self.plaidml_manager.device_active_experimental:
            device_name += " (experimental)"

        log_obj = {"file name": path.split('/')[-1].split('\\')[-1],
                   "file type": str(fleep.get(open(path, "rb").read(128)).extension),
                   "file duration": file_duration,
                   "sample rate": sr,
                   "framework": "PlaidML",
                   "device": str(device_name),
                   "inference_duration": inference_duration,
                   "results": syncpoints}
        self.logger.log(log_obj, "File Audio")

    def analyze(self, path: str) -> List[float]:
        """Analyzes one single file given its path.

        The file is imported as a one-dimensional (mono) array of values/samples.
        The array is segmented into one-second-chunks, sorted by the highest/loudest value within each second.
        From every chunk the MFCC features are extracted and stacked for inference.
        The inference reveals the second containing the clap sound.
        The spectral features are used again to determine the exact timestamp of the clap
        (a clap sound is loud and has a pretty even spectral distribution).

        Args:
            path: Path of the file that needs to be analyzed.

        Returns:
            A list of timestamps (in seconds), where clap sounds were found at (currently just one).
        """

        start_time = time.time()

        channels, sr = self.load(path)
        seconds = self.sort_seconds(channels, sr)
        maxima = self.get_maxima(channels, sr, seconds, len(seconds))  # currently all secs are used for better results.
        mfcc_stacked = self.stack_features(maxima, sr)
        prediction = self.predict(mfcc_stacked)

        index_of_second_with_clap = prediction.index(max(prediction))
        start_sample_of_second_with_clap = seconds[index_of_second_with_clap][-1]
        snippet_of_second_with_clap = maxima[index_of_second_with_clap]
        klapp_sample = start_sample_of_second_with_clap + self.find_clap_in_second(snippet_of_second_with_clap)
        syncpoint = [klapp_sample / sr]

        self.log(path, syncpoint, sr, librosa.get_duration(channels, sr), time.time()-start_time)
        return syncpoint

    def load(self, path: str) -> Tuple[np.ndarray, int]:
        """Loads a file from its path using the librosa package.

        Args:
            path: The path of the file that needs to be loaded.

        Returns:
            An array containing all the samples, as well as the sample rate of the file.
        """

        return librosa.load(path, mono=True, sr=None)

    def sort_seconds(self, channels: np.ndarray, sr: int) -> List[List[Union[int, float]]]:
        """Segments the audio into one-second chunks sorted by the loudest peak within them.

        Args:
            channels: The audio data that needs to be split.
            sr: The sample rate of the audio data.

        Returns:
            A list of lists (one for each second), each containing:
            * start = the index of the starting sample: 0, 48000, 96000, ...
            * pos = the index of the loudest sample (counting from start index): 420, 6900, 88, ...
            * value = the loudest value within the second (positioned at pos): 0.1234, 0.5678, 0.901, ...
            Looks like: [[0, 420, 0.1234], [48000, 6900, 0.5678], [96000, 88, 0.901], ...].
            It is sorted by value.
        """

        seconds = []
        for start in range(len(channels))[::sr]:
            end = min(start + sr - 1, len(channels))
            ch = channels[start:end]
            value = max(ch)
            pos = np.where(ch == value)[0][0]
            seconds.append([start, pos, value])
        seconds = sorted(seconds, reverse=True, key=lambda x: x[-1])
        return seconds

    def get_maxima(self, channels: np.ndarray, sr: int,
                   seconds: List[List[Union[int, float]]], amount: int) -> List[np.ndarray]:
        """Centers the loudest seconds around the loudest samples within them.

        Args:
            channels: The audio data that needs to be split.
            sr: The sample rate of the audio data.
            seconds: A list of lists characterizing seconds (has to come from sort_seconds function).
                Gets modified during this process.
            amount: The amount of maxima that need to be processed.
                If there are not enough seconds, all seconds will be processed.

        Returns:
            A list of the audio arrays of maxima, centered around the loudest peak.
        """

        maxima = []
        for i in range(min(amount, len(seconds))):
            start, pos, value = seconds[i]
            middle = start + pos
            start = middle - int(sr / 2)
            end = middle + int(sr / 2)
            if start < 0:
                end += abs(start)
                start = 0
            seconds[i].append(start)
            maxima.append(channels[start:end])
        return maxima

    def get_mfcc(self, channels: np.ndarray, sr: int, n_mfcc: int = 40) -> np.ndarray:
        """Extracts the two-dimensional MFCC feature matrix (40x94) of an audio snippet.

        Args:
            channels: The audio data to be converted to features.
            sr: The sample rate of the audio data.
            n_mfcc: Number of MFCC feature sets (rows).

        Returns:
            A two-dimensional matrix of the features (40x94). Can be used for inference with the CNN.
        """

        mfcc = librosa.feature.mfcc(y=channels, sr=sr, n_mfcc=n_mfcc)
        if mfcc.shape != (n_mfcc, 94):
            missing_cols = (94 - mfcc.shape[1])
            mfcc = np.pad(mfcc, ((0, 0), ((0, missing_cols))), "edge")
        return mfcc

    def stack_features(self, maxima: List[np.ndarray], sr: int) -> np.ndarray:
        """The features of multiple audio snippets are stacked on top of each other for faster inference.

        Args:
            maxima: The list of audio snippets to extract the features from.
            sr: The sample rate of the audio data.

        Returns:
            A stacked feature set, ready for inference.
        """

        mfcc_stacked = np.expand_dims(np.expand_dims(self.get_mfcc(maxima[0], sr), axis=2), axis=0)
        if len(maxima) > 1:
            for m in maxima[1::]:
                mfcc = np.expand_dims(np.expand_dims(self.get_mfcc(m, sr), axis=2), axis=0)
                mfcc_stacked = np.append(mfcc_stacked, mfcc, axis=0)
        return mfcc_stacked

    def predict(self, data: np.ndarray) -> List[float]:
        """Inferes the data using the machine learning model loaded during init.

        Args:
            data: The data in need of inference. Has to be a stack of 40x94 MFCC features.

        Returns:
            A list of confidences for each feature set.
        """

        prediction = self.model.predict(data)
        prediction = [klapp if klapp < 1 else klapp - noklapp for klapp, noklapp in prediction.astype(float)]
        return prediction

    def find_clap_in_second(self, second: np.ndarray) -> int:
        """Looks for the most likely position of the clap sound within a second of audio.

        A clap sound is usually the loudest sample within the second while having a pretty even spectrum.
        The function extracts the MFCC features from the second and identifies the column (one of 94)
        with the greatest sum, meaning the loudest one across the whole spectrum.
        Knowing the column it calculates the sample range in question and returns the position
        of the loudest sample within that range.

        Args:
            second: The second to be analyzed.

        Returns:
            The position of the most probable clap sound within the second.
        """

        mfcc = self.get_mfcc(second, len(second), n_mfcc=1)[0]
        mfcc_found = np.where(mfcc == max(mfcc))[0][0]
        mfcc_shortlist_start = max(0, (mfcc_found - 1)) * 512
        mfcc_shortlist_end = min(len(second) - 1, (mfcc_found + 1)) * 512
        mfcc_shortlist = second[mfcc_shortlist_start: mfcc_shortlist_end]
        found = np.where(mfcc_shortlist == max(mfcc_shortlist))[0][0]
        found += mfcc_shortlist_start
        return found