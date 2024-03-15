import sys
import numpy as np
import librosa
import audioread
from birdnetlib.exceptions import AudioFormatError

sys.path.append("../../src/iSparrow")
from src.iSparrow import preprocessor_base as ppb


class Preprocessor(ppb.PreprocessorBase):
    """
    Preprocessor Preprocess audio data into resampled chunks for analysis.

    """

    def __init__(
        self,
        sample_rate: int = 48000,
        overlap: float = 0.0,
        sample_secs: int = 3.0,
        resample_type: str = "kaiser_fast",
    ):
        """
        __init__ Construct a new preprocesssor for custom birdnet classifiers from given parameters, and use defaults for the ones not present.

        Args:
            sample_rate (int, optional): The sample rate used to resample the read audio file. Defaults to 48000.
            overlap (float, optional): Overlap between chunks to be analyzed. Defaults to 0.0.
            sample_secs (int, optional): Length of chunks to be analyzed at once. Defaults to 3.0.
            resample_type (str, optional): Resampling method used when reading from file. Defaults to "kaiser_fast".
        """
        self.sample_rate = sample_rate
        self.overlap = overlap
        self.sample_secs = sample_secs
        self.resample_type = resample_type
        self.duration = 0
        self.actual_sampling_rate = 0
        self.chunks = []
        super().__init__("birdnet_defaults_preprocessor")

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
        try:
            data, rate = librosa.load(
                path, sr=self.sample_rate, mono=True, res_type=self.resample_type
            )

            self.duration = librosa.get_duration(y=data, sr=self.sample_rate)
            self.actual_sampling_rate = rate

        # README: on macos, the Exception below is thrown, no ubuntu the AudioFormatError...
        except audioread.exceptions.NoBackendError as e:
            print(e)
            raise AudioFormatError("Audio format could not be opened.")
        except FileNotFoundError as e:
            print(e)
            raise e
        except Exception as e:
            print(e)
            raise AudioFormatError("Generic audio read error occurred from librosa.")

        print(" data: ", len(data), rate, self.duration)
        return data

    def process_audio_data(self, rawdata: np.ndarray) -> list:
        """
        process_audio_data Process raw, resampled audio data into chunks that then can be analyzed

        Args:
            data (np.ndarray): raw, resampled audio data as returned from 'read_audio'

        Returns:
            list: chunked audio data
        """
        print("process audio data custom")
        seconds = self.sample_secs
        minlen = 1.5

        self.chunks = []

        for i in range(
            0, len(rawdata), int((seconds - self.overlap) * self.sample_rate)
        ):

            split = rawdata[i : (i + int(seconds * self.actual_sampling_rate))]

            # End of signal?
            if len(split) < int(minlen * self.actual_sampling_rate):
                break

            # Signal chunk too short? Fill with zeros.
            if len(split) < int(self.actual_sampling_rate * seconds):
                temp = np.zeros((int(self.actual_sampling_rate * seconds)))
                temp[: len(split)] = split
                split = temp

            self.chunks.append(split)

        print(
            "process audio data custom: complete, read ",
            str(len(self.chunks)),
            "chunks.",
        )

        return self.chunks


def preprocessor_from_config(cfg: dict) -> Preprocessor:
    """
    preprocessor_from_config Construct a new preprocessor from a given dictionary. This represents typically a config node read from a YAML file.

    Args:
        cfg (dict): Config node read from a YAML file

    Returns:  new preprocessor instance
    """
    return Preprocessor(**cfg)
