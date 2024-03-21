
import numpy as np

from tensorflow.signal import frame as tf_split_signal_into_chunks

from iSparrow import preprocessor_base as ppb


# README: work in progress - will be completed in separate issue
class Preprocessor(ppb.PreprocessorBase):
    """
    Preprocessor Preprocess audio data into resampled chunks for analysis.

    """

    def __init__(
        self,
        sample_rate: int = 32000,
        sample_secs: float = 5.0,
        resample_type: str = "kaiser_fast",
    ):
        """
        __init__ Construct a new preprocesssor for custom birdnet classifiers from given parameters, and use defaults for the ones not present.

        Args:
            sample_rate (int, optional): The sample rate used to resample the read audio file. Defaults to 48000.
            sample_secs (float, optional): Length of chunks to be analyzed at once. Defaults to 3.0.
            resample_type (str, optional): Resampling method used when reading from file. Defaults to "kaiser_fast".
        """
        # README: this class does not have an overlap attribute because the model it works with does not want it.
        super().__init__(
            "google_perch",
            sample_rate=sample_rate,
            sample_secs=sample_secs,
            resample_type=resample_type,
        )

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
            "sample_secs",
            "resample_type",
            "duration",
            "actual_sampling_rate",
        ]

        if len([key for key in cfg if key not in allowed]) > 0:
            raise RuntimeError("Erroneous keyword arguments in preprocessor config")

        return cls(**cfg)
