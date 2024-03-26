import librosa
from pvrecorder import PvRecorder
from abc import ABC, abstractmethod


class AudioSourceBase:
    def __init__(
        self, data_sink: str = None, length: int = 30, sample_rate: int = 32000
    ):
        self.length_in_s = (length,)
        self.sample_rate = sample_rate
        self.data_sink = data_sink

    @abstractmethod
    def record_audio(self):
        pass


class ARecord:
    pass


class PvRecorder:
    pass
