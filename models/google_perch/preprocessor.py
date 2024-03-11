import numpy as np
import librosa
import audioread
from scipy.signal import resample
from tensorflow import signal


class Preprocessor:

    def __init__(
        self,
        sample_rate: int = 48000,
        overlap: float = 0.0,
        sample_secs: float = 3.0,
        resample_type="kaiser_fast",
    ):
        """TODO

        Args:
            sample_rate (int, optional): _description_. Defaults to 48000.
            overlap (float, optional): _description_. Defaults to 0..
            sample_secs (float, optional): _description_. Defaults to 3.0.
            resample_type (str, optional): _description_. Defaults to 'kaiser_fast'.
        """
        self.sample_rate = sample_rate
        self.overlap = overlap
        self.sample_secs = sample_secs
        self.rawaudio = None
        self.resample_type = resample_type
        self.duration = 0
        self.chunks = []

    def ensure_sample_rate(self, data: np.array, actual_rate: int):
        """taken over from https://www.kaggle.com/code/pratul007/bird-species-classification-using-tensorflow-hub

        Args:
            data (np.array): _description_
            actual_rate (int): _description_
        """

        num_samples = len(data)

        original_duration = num_samples / original_sample_rate

        time_old = np.linspace(0, original_duration, num_samples)

        time_new = np.linspace(
            0,
            original_duration,
            int(num_samples * desired_sample_rate / original_sample_rate),
        )

        waveform = resample(
            raw_data, int(num_samples * desired_sample_rate / original_sample_rate)
        )

        sample_rate = desired_sample_rate

        return sample_rate, waveform

    def read_audio_data(self, path: str):
        """Read an audio file into a 1D numpy array.

        Args:
            path (str): path to the audio file to read

        Raises:
            AudioFormatError: If the audioformat is unknown to librosa
            FileNotFoundError: File doesn't exist
            BaseException: Generic error if anything else goes wrong
        """
        print("read audio data")

        try:
            rawaudio, rate = librosa.load(
                path, sr=self.sample_rate, mono=True, res_type=self.resample_type
            )
            self.duration = librosa.get_duration(y=self.rawaudio, sr=self.sample_rate)
        except audioread.exceptions.NoBackendError as e:
            print(e)
            raise AudioFormatError("Audio format could not be opened.")
        except FileNotFoundError as e:
            print(e)
            raise e
        except BaseException as e:
            print(e)
            raise AudioFormatError("Generic audio read error occurred from librosa.")

        self.process_audio_data(raw_audio, rate)

    def process_audio_data(self, raw_audio, actual_rate):
        """Process audio data for use with the google perch model obtained from tensorflow-hub.
        Implementation template for classification can be seen here: https://www.kaggle.com/code/pratul007/bird-species-classification-using-tensorflow-hub/notebook

        Args:
            actual_rate: the sampling rate after resampling by librosa, returned from librosa.load
        """

        # ensure desired sample rate (actual rate may be different?)
        if acutal_rate != self.sample_rate:
            # sampling rate isn't quite what we want -> resample again via scipy
            sample_rate, raw_audio = self.ensure_sample_rate(raw_audio, actual_rate)

        # chop audio data into chunks of length 'self.sample_secs
        self.chunks = []

        overlap_length = self.overlap * self.sample_rate
        frame_length = self.sample_secs * self.sample_rate
        step_length - frame_length - ovelap_length
        self.chunks = signal.frame(
            self.rawaudio, frame_length, step_length, pad_end=True
        )

        # ensure desired sample rate (actual rate may be different?)
