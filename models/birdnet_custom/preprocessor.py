import numpy as np
import librosa
import audioread


class Preprocessor:
    """_summary_"""

    def __init__(self, cfg: dict):
        """_summary_

        Args:
            sample_rate (int, optional): _description_. Defaults to 48000.
            overlap (float, optional): _description_. Defaults to 0..
            sample_secs (float, optional): _description_. Defaults to 3.0.
            resample_type (str, optional): _description_. Defaults to 'kaiser_fast'.
        """
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
        print(path, self.sample_rate)
        # Open file with librosa (uses ffmpeg or libav)
        try:
            data, rate = librosa.load(
                path, sr=self.sample_rate, mono=True, res_type=self.resample_type
            )
            self.duration = librosa.get_duration(y=data, sr=self.sample_rate)

        except audioread.exceptions.NoBackendError as e:
            print(e)
            raise AudioFormatError("Audio format could not be opened.")
        except FileNotFoundError as e:
            print(e)
            raise e
        except BaseException as e:
            print(e)
            raise AudioFormatError("Generic audio read error occurred from librosa.")

        return self.process_audio_data(rate, data)

    def process_audio_data(self, rate: int, data: float):
        """_summary_

        Args:
            rate (int): _description_
            data (nd.array): _description
        """
        # Split audio into 3-second chunks

        # Split signal with overlap
        seconds = self.sample_secs
        minlen = 1.5

        # what about the bandpass that they use in the Analyzer package. This should definitely be here.
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

        return chunks
