from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import pyaudio
import wave


class RecorderBase(ABC):
    """
    RecorderBase Abstract base class for any audio recording functionality that shall be used with iSparrow.

    Attributes
    ----------
    length_in_s (int) : Length of each recorded chunk in seconds.
    sample_rate (int) : Sample rate of recording
    output_folder (str) : The output folder to write data to
    file_type (str) : File type to save recorded data as, e.g., wave, mp3, raw...
    channels (int) : Number of recording channels. Depends on used hardware and desired quality.
    num_format : The format for each recorded data point. Depends on the library used
    mode (str) : The mode in which a recorder should operate. Either 'stream' (don't save recorded data to file) or 'record' (save recorded data to file).

    Methods:
    --------
    start(stop_condition = lambda x: False): Make the caller start generate data. Runs until 'stop_condition(self)' returns True. Abstract method that needs to be implemented by derived class.
    stream_audio(): Get a chunk of recorded data corresponding to 'length_in_s' seconds of recording. Abstract method that needs to be implemented by derived class.
    stop(): Stop recorder. Abstract method that needs to be implemented by derived class.
    """

    def __init__(
        self,
        output_folder: str = None,
        length_s: int = 15,
        sample_rate: int = 32000,
        file_type: str = "wave",
        channels: int = 1,
        mode: str = "record",
        num_format=None,
    ):
        """
        __init__ Create a new instance. This class should not be instantiated on its own, but only as part of a child class.


        Args:
            output_folder (str, optional): Output folder to write files to. Defaults to None.
            length_s (int, optional): Lenght of each recorded chunk of data in seconds. Defaults to 15.
            sample_rate (int, optional): Sample rate of recording. Defaults to 32000.
            file_type (str, optional): File type to save files as. Defaults to "wav".
            channels (int, optional): Number of used channels for recording. Defaults to 1.
            mode (str, optional): Mode of operation. Can be 'record' or 'stream'. Defaults to "record".
            num_format (optional): Numerical format for each sample that is recorded. Depends on the library used for implementing the recording process. Defaults to None.

        Raises:
            ValueError: _description_
        """
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
        channels: int = 1,
        mode: str = "record",
        input_device_index: int = None,
    ):
        """
        __init__ Create a new instance.

        Args:
            output_folder (str, optional): Folder to write data files to in 'record' mode. Defaults to None.
            length_s (int, optional): Length in seconds of each data chunk that is returned (mode = 'stream') or data file written (mode = 'record'). Defaults to 15.
            sample_rate (int, optional): Sample rate used for recording. Defaults to 32000.
            channels (int, optional): Number of channels used for recording. Possible number depends on recording hardware. Defaults to 1.
            mode (str, optional): Operational mode. Can either be 'record' (write data to file) or 'stream' (don't write data to file and return recorded data upon request). Defaults to "record".
            input_device_index (int, optional): Pyaudio device index that identifies the device to be used for recording. If 'None', default device is used.. Defaults to None.

        Raises:
            ValueError: _description_
        """
        self.p = pyaudio.PyAudio()

        self.stream = None

        if mode == "record":

            if output_folder is None:
                raise ValueError(
                    "Output folder for recording object cannot be None in 'record' mode"
                )

            self.filename_fromat = "%y%m%d_%H%M%S.wav"

        self.input_device_index = input_device_index

        super().__init__(
            output_folder=output_folder,
            length_s=length_s,
            sample_rate=sample_rate,
            file_type="wave",
            channels=channels,
            mode=mode,
            num_format=pyaudio.paInt16,
        )

    def start(self, stop_condition: callable = lambda x: False):
        """
        start Start the pyaudio input stream such that data is gathered. If self.mode is 'record', write wave files of 'self.length_in_s' seconds length to disk into 'self.output_folder'.

        Args:
            stop_condition (_type_, optional): Only relevant for self.mode = 'record'. Callable that returns True when the recording process should be stopped. Is checked each time a file is written, i.e., every 'self.length_in_s' seconds of recording. Defaults to lambda x:False.

        Raises:
            e: Generic exception if an error occurs during recording data or writing to file.
        """
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

                    length, frames = self.stream_audio()

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
        """
        stop Stop the recording process, close the input data stream and release all resources the instance holds via pyaudio.
        """

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
        """
        stream_audio Get a chunk of recorded data that corresponds to 'self.length_in_s' seconds of audio.

        Returns:
            Tuple[int, bytes]: Tuple containing the number of bytes in the recorded chunk, and the recorded data as raw bytes buffer.
        """

        chunk_size = int(self.sample_rate / 100)

        frames = b"".join(
            [
                self.stream.read(chunk_size)
                for i in range(0, int(self.sample_rate / chunk_size * self.length_in_s))
            ]
        )

        return len(frames), frames

    @classmethod
    def from_cfg(cls, cfg: dict):
        """
        from_cfg Creates a new `Recorder` instance. All arguments not given in the `cfg` argument are filled with default values of the constructor.

        Args:
            cfg (dict): Dictionary, obtained from reading a yaml config file, that contains the keyword arguments to construct the `Recorder` from.

        Raises:
            ValueError: When the supplied dictionary does not have an 'output_folder' node.

        Returns:
           Recorder : A new instance of the `Recorder` class, built with the supplied arguments.
        """

        if "output_folder" not in cfg:
            raise ValueError("Output folder must be given in config node for recorder.")

        folder = Path(cfg["output_folder"]).expanduser()

        cfg["output_folder"] = folder

        return cls(**cfg)
