from abc import ABC, abstractmethod
import numpy as np
import librosa
import audioread


class AudioFormatError(Exception):
    pass


class PreprocessorBase(ABC):
    """
    PreprocessorBase A common interface for all custom preprocessor classes

    """

    def __init__(
        self,
        name: str,
        sample_rate: int = 32000,
        sample_secs: float = 5.0,
        overlap: float = 0.0,
        resample_type: str = "kaiser_fast",
    ):
        self.name = name
        self.sample_rate = sample_rate
        self.overlap = overlap
        self.sample_secs = sample_secs
        self.resample_type = resample_type
        self.duration = 0
        self.actual_sampling_rate = 0
        self.chunks = []

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

        try:
            data, rate = librosa.load(
                path, sr=self.sample_rate, mono=True, res_type=self.resample_type
            )

            self.duration = librosa.get_duration(y=data, sr=self.sample_rate)
            self.actual_sampling_rate = rate

        except audioread.exceptions.NoBackendError as e:
            raise AudioFormatError("Audio format could not be opened.") from e
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            raise AudioFormatError(
                "Generic audio read error occurred from librosa."
            ) from e

        if self.actual_sampling_rate != self.sample_rate:
            raise RuntimeError(
                "Error, sampling rate from resampling and desired sampling rate don't match"
            )

        return data

    @abstractmethod
    def process_audio_data(self, rawdata: np.ndarray) -> list:
        """
        process_audio_data Receives raw read data and processes it into something that can be used by the analyzer model.


        Args:
            rawdata (np.ndarray): Raw audiodata received from the read_audio_data function.

        Returns:
            list: final preprocessed audiodata ready to be passed to the analyzer
        """

        pass
