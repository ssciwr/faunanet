from abc import ABC, abstractmethod
from datetime import datetime
import subprocess
from pathlib import Path
import warnings
import platform
import pyaudio
import wave


class RecorderBase(ABC):
    def __init__(
        self,
        data_sink: str = None,
        length_s: int = 15,
        sample_rate: int = 32000,
        file_type: str = "wav",
        channels: int = 1,
        mode: str = "record",
    ):
        self.length_in_s = length_s
        self.sample_rate = sample_rate
        self.data_sink = data_sink
        self.file_type = file_type
        self.channels = channels

        if mode not in ["record", "stream"]:
            raise ValueError("Unknown mode. Must be 'record', 'stream'")

        self.mode = mode

    @abstractmethod
    def start(
        self,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ):
        pass

    @abstractmethod
    def stream_audio(self, chunksize="auto"):
        pass

    @abstractmethod
    def stop(self, timeout: int = 30):
        pass


class ARecord(RecorderBase):
    # FIXME: this must go away: birdnetlib uses it, but pyaudio is probably a better choice here because it's better integrated than a callback to an external dependency
    def __init__(
        self,
        output_folder: str = None,
        length_s: int = 15,
        sample_rate: int = 32000,
        num_format: str = "S16_LE",
        file_type: str = "wav",
        channels: int = 1,
        mode="record",
    ):

        if platform.system() != "Linux":
            raise RuntimeError("arecord based Recorder only supported on linux")

        if num_format != "S16_LE":
            warnings.warn(
                "Non-Standard sample format found. You MUST set the sample_width attribute of this class by hand before recording data"
            )

        self.num_format = num_format

        self.file_type = file_type

        self.channels = channels

        self.sample_width = 2

        self.process = None

        self.process_output = None

        self.process_errors = None

        self.cmd = [
            "arecord",
            "-f",  # format for individual samples
            str(self.num_format),
            "-r",
            str(sample_rate),
            "--fatal-errors",
            "-c",  # channels
            str(self.channels),
            "-t",  # file type: wav, raw, mp3..
            str(self.file_type),
        ]

        if mode == "record":

            if output_folder is None:
                raise ValueError("Output folder for recording object cannot be None")

            self.filename_fromat = "%y%m%d_%H%M%S.wav"

            data_sink = str(Path(output_folder) / self.filename_fromat)

            self.cmd.append(
                "--use-strftime",
            )

            self.cmd.extend(
                [
                    "--max-file-time",
                    str(length_s),
                ]
            )

            self.cmd.append(data_sink)
        else:
            data_sink = None

        super().__init__(
            data_sink=data_sink, length_s=length_s, sample_rate=sample_rate, mode=mode
        )

    def start(
        self,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ):
        self.process = subprocess.Popen(
            self.cmd,
            stdin=stdin,
            stderr=stderr,
            stdout=stdout,
        )

    def stream_audio(self, chunksize="auto"):

        if self.mode == "record":
            raise ValueError("Cannot stream audio in 'record' mode")

        if chunksize == "auto":
            data_size = (
                self.channels * self.sample_rate * self.length_in_s * self.sample_width
            )
        else:
            data_size = chunksize
        # make timestamps that say from when to when this was recorded

        start = datetime.now().strftime("%y%m%d_%H%M%S")

        audio_chunk_data = self.process.stdout.read(data_size)

        stop = datetime.now().strftime("%y%m%d_%H%M%S")

        print(len(audio_chunk_data), data_size)

        return start, stop, audio_chunk_data

    def check(self):

        if self.process is not None:
            return self.process.poll()
        else:
            return -1

    def get_process_output(self):

        process_output, _ = self.process.communicate()

        self.process_output = process_output.decode("utf-8")

        return self.process_output

    def get_process_errors(self):
        _, process_errors = self.process.communicate()

        self.process_errors = process_errors.decode("utf-8")

        return self.process_errors

    def stop(self, timeout: int = 30):

        process_return_code = self.check()
        if (
            process_return_code is None and process_return_code != -1
        ):  # process has not yet finished

            try:
                self.process.terminate()

                self.process.wait(
                    timeout=timeout,
                )

                process_output, process_errors = self.process.communicate()

                self.process_output = process_output.decode("utf-8")

                self.process_errors = process_errors.decode("utf-8")

            except subprocess.TimeoutExpired as e:
                print(e)
                self.process.kill()
                out, errs = self.process.communicate()
        else:
            return process_return_code


class Recorder(RecorderBase):

    def __init__(
        self,
        output_folder: str = None,
        length_s: int = 15,
        sample_rate: int = 32000,
        num_format: str = pyaudio.paFloat32,
        file_type: str = "wav",
        channels: int = 1,
        mode="record",
        input_device_index: int = None,
    ):

        if mode == "record":

            if output_folder is None:
                raise ValueError("Output folder for recording object cannot be None")

            self.filename_fromat = "%y%m%d_%H%M%S.wav"

        self.input_device_index = input_device_index

        super().__init__(
            data_sink=output_folder,
            length_s=length_s,
            sample_rate=sample_rate,
            file_type=file_type,
            channels=channels,
            mode=mode,
        )

        self.p = pyaudio.PyAudio()
        self.stream = None

    def start(self):
        self.p.open(
            format=format,
            channels=self.channels,
            rate=self.sample_rate,
            input_device_index=self.input_device_index,
            input=False,
            start=True,
            frames_per_buffer=self.sample_rate * self.length_in_s,
        )

        if self.mode == "record":

            filename = datetime.now().strftime(self.filename_fromat) + ".wav"

            with wave.open(Path(self.data_sink) / filename) as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.num_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(
                    b"".join(
                        [
                            self.stream.read(self.sample_rate)
                            for i in range(0, self.length_in_s)
                        ]
                    )
                )

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def __del__(self):
        self.stop()

    def stream_audio(self):
        return self.stream.read(self.sample_rate * self.length_in_s)
