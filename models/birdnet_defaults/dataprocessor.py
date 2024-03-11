import numpy as np
import librosa

# import the base class
from iSparrow import sparrow_preprocessor_abstract as spa


class Preprocessor(spa.AbstractDataProcessor):
    """_summary_"""

    def __init__(self, cfg: dict):

        self.sample_rate = cfg["sample_rate"]
        self.overlap = cfg["overlap"]
        self.sample_secs = cfg["sample_secs"]
        self.resample_type = cfg["resample_type"]

    def read_audio_data(self, path):
        """_summary_

        Args:
            path (_type_): _description_

        Raises:
            AudioFormatError: _description_
            e: _description_
            AudioFormatError: _description_

        Returns:
            _type_: _description_
        """
        print("read_audio_data birdnet default")
        # Open file with librosa (uses ffmpeg or libav)
        try:
            data, rate = librosa.load(
                path, sr=self.sample_rate, mono=True, res_type=self.resample_type
            )
            duration = librosa.get_duration(y=self.ndarray, sr=self.sample_rate)

        except audioread.exceptions.NoBackendError as e:
            print(e)
            raise AudioFormatError("Audio format could not be opened.")
        except FileNotFoundError as e:
            print(e)
            raise e
        except BaseException as e:
            print(e)
            raise AudioFormatError("Generic audio read error occurred from librosa.")

        return self.process_audio_data(data, rate)

    def process_audio_data(self, data, *args, **kwargs):
        """_summary_

        Args:
            rate (_type_): _description_
        """
        print("process audio birdnet default")

        rate = args[1]  # get actual sampling rate
        # Split audio into 3-second chunks

        # Split signal with overlap
        seconds = self.sample_secs
        minlen = 1.5

        chunks = []

        for i in range(0, len(data), int((seconds - self.overlap) * self.sample_rate)):

            split = data[i : i + int(seconds * rate)]

            # End of signal?
            if len(split) < int(minlen * rate):
                break

            # Signal chunk too short? Fill with zeros.
            if len(split) < int(rate * seconds):
                temp = np.zeros((int(rate * seconds)))
                temp[: len(split)] = split
                split = temp

            chunks.append(split)

        print("read_audio_data: complete, read ", str(len(chunks)), "chunks.")

        return chunks
