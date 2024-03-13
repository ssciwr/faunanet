import numpy as np
import librosa
import audioread
from birdnetlib.exceptions import AudioFormatError

from iSparrow import preprocessor_base as ppb

# README: work in progress - will be completed in separate issue
class Preprocessor(ppb.PreprocessorBase):
    """
    Preprocessor Preprocess audio data into resampled chunks for analysis.

    """

    def __init__(self, cfg: dict):
        """
        __init__ Create a new data processor.

        Reads in audio data and processes them, ready to be analyzed by the analyzer of bridnetlib.

        Args:
            cfg (dict): config node for preprocessing
        """
        self.sample_rate = cfg["sample_rate"]
        self.overlap = cfg["overlap"]
        self.sample_secs = cfg["sample_secs"]
        self.resample_type = cfg["resample_type"]
        self.duration = 0
        self.actual_sampling_rate = 0
        super().__init__("google_perch")

    def read_audio_data(self, path: str) -> np.ndarray:
        """
        read_audio_data Read in audio data, resample and return the resampled raw data, adding members for actual sampling rate and duration of audio file.
        Args:
            path (str): Path to the audio file to be analyzed

        Raises:
            AudioFormatError: When the format of the audio file is unknown

        Returns:
            np.ndarray: resampled raw data
        """

        print("read audio file custom")

        return np.array([])

    def process_audio_data(self, rawdata: np.ndarray) -> list:
        """
        process_audio_data Process raw, resampled audio data into chunks that then can be analyzed

        Args:
            data (np.ndarray): raw, resampled audio data as returned from 'read_audio'

        Returns:
            list: chunked audio data
        """
        print("process audio data custom ")
        chunks = []
        print("process audio data custom: complete, read ", str(len(chunks)), "chunks.")

        return chunks
