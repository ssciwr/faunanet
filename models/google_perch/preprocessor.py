import sys

sys.path.append("../../src/iSparrow")
import numpy as np
import librosa
import audioread
from birdnetlib.exceptions import AudioFormatError
from tensorflow.signal import frame as tf_split_signal_into_chunks

from src.iSparrow import preprocessor_base as ppb


# README: work in progress - will be completed in separate issue
class Preprocessor(ppb.PreprocessorBase):
    """
    Preprocessor Preprocess audio data into resampled chunks for analysis.

    """

    def __init__(
        self,
        sample_rate: int = 32000,
        sample_secs: float = 5.0,
        overlap: float = 0.0,
        resample_type: str = "kaiser_fast",
    ):
        """
        __init__ Construct a new preprocesssor for custom birdnet classifiers from given parameters, and use defaults for the ones not present.

        Args:
            sample_rate (int, optional): The sample rate used to resample the read audio file. Defaults to 48000.
            overlap (float, optional): Overlap between chunks to be analyzed. Defaults to 0.0.
            sample_secs (float, optional): Length of chunks to be analyzed at once. Defaults to 3.0.
            resample_type (str, optional): Resampling method used when reading from file. Defaults to "kaiser_fast".
        """
        self.sample_rate = sample_rate
        self.overlap = overlap
        self.sample_secs = sample_secs
        self.resample_type = resample_type
        self.duration = 0
        self.actual_sampling_rate = 0
        super().__init__("google_perch")

    def read_audio_data(self, path: str) -> np.array:
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

        try:
            data, rate = librosa.load(
                path, sr=self.sample_rate, mono=True, res_type=self.resample_type
            )

            self.duration = librosa.get_duration(y=data, sr=self.sample_rate)
            self.actual_sampling_rate = rate

        except audioread.exceptions.NoBackendError as e:
            print(e)
            raise AudioFormatError("Audio format could not be opened.")
        except FileNotFoundError as e:
            print(e)
            raise e
        except Exception as e:
            print(e)
            raise AudioFormatError("Generic audio read error occurred from librosa.")

        if self.actual_sampling_rate != self.sample_rate:
            raise RuntimeError(
                "Error, sampling rate from resampling and desired sampling rate don't match"
            )

        return data

    def process_audio_data(self, rawdata: np.array) -> np.array:
        """
        process_audio_data Process raw, resampled audio data into chunks that then can be analyzed

        Args:
            data (np.ndarray): raw, resampled audio data as returned from 'read_audio'

        Returns:
            list: chunked audio data
        """
        print("process audio data custom ")

        self.chunks = []

        # README: this is the usual birdnet/birdnetlib splitting code...
        # minlen = 1.5

        # step = int(self.sample_secs * self.sample_rate)

        # for i in range(0, len(rawdata), step):

        #     split = rawdata[i : (i + int(self.sample_secs * self.actual_sampling_rate))]

        #     # end of data: throw away tails that are too short
        #     if len(split) < int(minlen * self.actual_sampling_rate):
        #         break

        #     # pad data
        #     if len(split) < int(self.sample_secs * self.actual_sampling_rate):
        #         temp = np.zeros(int(self.sample_secs * self.actual_sampling_rate))
        #         temp[: len(split)] = split
        #         split = temp

        #     self.chunks.append(split)

        # README: ... but used instead tensorflow code as suggested in https://www.kaggle.com/code/pratul007/bird-species-classification-using-tensorflow-hub.
        # because it has the functionality built index

        # raise when sampling rate is unequal.
        if self.actual_sampling_rate != self.sample_rate:
            raise RuntimeError(
                "Sampling rate is not the desired one. Desired sampling rate: {self.sample_rate}, actual sampling rate: {self.actual_sampling_rate}"
            )

        frame_length = int(self.sample_secs * self.sample_rate)
        step_length = int(self.sample_secs - self.overlap) * self.sample_rate

        self.chunks = tf_split_signal_into_chunks(
            rawdata, frame_length, step_length, pad_end=True
        ).numpy()

        print(
            "process audio data google: complete, read ",
            str(len(self.chunks)),
            "chunks.",
        )

        return self.chunks

    @classmethod
    def from_cfg(cls, cfg: dict):

        # make sure there are no more than the allowed keyword arguments in the cfg
        allowed = [
            "sample_rate",
            "overlap",
            "sample_secs",
            "resample_type",
            "duration",
            "actual_sampling_rate",
        ]

        if len([key for key in cfg if key not in allowed]) > 0:
            raise RuntimeError("Erroneous keyword arguments in preprocessor config")

        return cls(**cfg)
