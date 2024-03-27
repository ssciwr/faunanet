from abc import ABC, abstractmethod
from datetime import datetime
import subprocess
from pathlib import Path
import pyaudio
import wave


class RecorderBase(ABC):
    def __init__(
        self,
        output_folder: str = None,
        length_s: int = 15,
        sample_rate: int = 32000,
        file_type: str = "wav",
        channels: int = 1,
        mode: str = "record",
        num_format=None,
    ):
        self.length_in_s = length_s
        self.sample_rate = sample_rate
        self.output_folder = output_folder
        self.file_type = file_type
        self.channels = channels
        self.num_format = num_format
        if mode not in ["record", "stream"]:
            raise ValueError("Unknown mode. Must be 'record', 'stream'")

        self.mode = mode

    @property
    def output(self):
        return str(Path(self.output_folder).absolute())

    @abstractmethod
    def start(self, stop_condition: callable = lambda x: False):
        pass

    @abstractmethod
    def stream_audio(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class Recorder(RecorderBase):

    def __init__(
        self,
        output_folder: str = None,
        length_s: int = 15,
        sample_rate: int = 32000,
        file_type: str = "wav",
        channels: int = 1,
        mode: str = "record",
        input_device_index: int = None,
    ):

        if mode == "record":

            if output_folder is None:
                raise ValueError("Output folder for recording object cannot be None")

            self.filename_fromat = "%y%m%d_%H%M%S.wav"

        self.input_device_index = input_device_index

        super().__init__(
            output_folder=output_folder,
            length_s=length_s,
            sample_rate=sample_rate,
            file_type=file_type,
            channels=channels,
            mode=mode,
            num_format=pyaudio.paInt16,
        )

        self.p = pyaudio.PyAudio()
        self.stream = None

    def start(self, stop_condition: callable = lambda x: False):

        chunk_size = int(self.sample_rate / 100)

        try:
            self.stream = self.p.open(
                format=self.num_format,
                channels=self.channels,
                rate=self.sample_rate,
                input_device_index=self.input_device_index,
                input=True,
                start=True,
                frames_per_buffer=chunk_size,
            )

            if self.mode == "record":

                # while True:
                while stop_condition(self) is False:

                    filename = datetime.now().strftime(self.filename_fromat)

                    frames = self.stream_audio()

                    with wave.open(
                        str(Path(self.output_folder) / filename), "wb"
                    ) as wavfile:

                        wavfile.setnchannels(self.channels)

                        wavfile.setsampwidth(self.p.get_sample_size(self.num_format))

                        wavfile.setframerate(self.sample_rate)

                        wavfile.writeframes(frames)
        except Exception as e:
            self.stop()  # release resources that of portaudio, then reraise
            raise e

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if self.p is not None:
            self.p.terminate()
            self.p = None

    def __del__(self):
        self.stop()

    def stream_audio(self):

        chunk_size = int(self.sample_rate / 100)

        frames = b"".join(
            [
                self.stream.read(chunk_size)
                for i in range(0, int(self.sample_rate / chunk_size * self.length_in_s))
            ]
        )

        return frames

    @classmethod
    def from_cfg(cls, cfg: dict):

        if "output_folder" not in cfg:
            raise ValueError("Output folder must be given in config node for recorder.")

        folder = Path(cfg["output_folder"]).expanduser()

        cfg["output_folder"] = folder

        default = {
            "length_s": 15,
            "sample_rate": 32000,
            "file_type": "wav",
            "channels": 1,
            "mode": "record",
            "input_device_index": None,
        }

        kwargs = default | cfg

        print(kwargs)

        return cls(**kwargs)
