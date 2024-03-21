# import sys
import numpy as np
import iSparrow.preprocessor_base as ppb


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

        super().__init__(
            "birdnet_defaults_preprocessor",
            sample_rate=sample_rate,
            overlap=overlap,
            sample_secs=sample_secs,
            resample_type=resample_type,
        )

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

    @classmethod
    def from_cfg(cls, cfg: dict):
        """
        from_cfg Construct a new preprocessor from a given dictionary. This represents typically a config node read from a YAML file.

        Args:
            cfg (dict): Config node read from a YAML file

        Returns:  new preprocessor instance
        """
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
