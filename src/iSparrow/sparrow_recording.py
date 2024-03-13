import os
import numpy as np
from pathlib import Path
import datetime
from birdnetlib.main import RecordingBase
from birdnetlib.analyzer import Analyzer
from .preprocessor_base import PreprocessorBase


class SparrowRecording(RecordingBase):
    """
    SparrowRecording A SparrowRecording represents an audio recoding of arbitrary length and date associated with a preprocessor and analyzer object. 

    SparrowRecordings read and preprocess audio data using the supplied preprocessor object and can use the 'analyzer' object to analyze and classify the contained animal sounds

    Args:
        RecordingBase (birdnetlib.RecordingBase): See documentation of the birdnetlib.RecordingBase class
    """

    def __init__(
        self,
        analyzer: Analyzer,
        preprocessor: PreprocessorBase,
        path: str,
        week_48: int = -1,
        date: datetime = None,
        lat: float = None,
        lon: float = None,
        return_all_detections: bool = False,
        min_conf: float = 0.25
    ):
        """
        Create a new SparrowRecording.

        Args:
            analyzer (Analyzer): Analyzer object to use. Contains model to use for analysis as well as result post processing.
            preprocessor (PreprocessorBase): Preprocessor object to use. Must adhere to the interface defined in iSparrow.preprocessor_base.
            path (str): Path to the audio file to be analyzed
            week_48 (int, optional): Week in the calendar. Defaults to -1.
            date (datetime, optional): Date of recording. Alternative to 'week'. Defaults to None.
            sensitivity (float, optional): Detection sensitivity. Defaults to 1.0.
            lat (float, optional): Latitude. If latitude and longitude are given, the species list is predicted first.  Defaults to None.
            lon (float, optional): Longitude. If latitude and longitude are given, the species list is predicted first.  Defaults to None.
            min_conf (float, optional): Minimal confidence to use to consider a detection valid. Defaults to 0.1.
            return_all_detections (bool, optional): Ignore confidence and return all detections we got. Defaults to False.
        """
        self.processor = preprocessor
        self.path = path
        p = Path(self.path)
        self.filestem = p.stem

        # README: This call will change later, as some of the members will live in the analyzer/model in future PR
        super().__init__(analyzer, week_48=week_48, date=date, sensitivity=1.0, lat=lat, lon=lon, min_conf=min_conf, overlap=0.0, return_all_detections=return_all_detections)

    @property
    def filename(self):
        return os.path.basename(self.path)

    # @property
    # def sample_secs(self):
    #     return self.processor.sample_secs

    # @property
    # def overlap(self):
    #     return self.processor.overlap

    @property
    def chunks(self):
        return self.processor.chunks

    def process_audio_data(self, data: np.ndarray) -> list:
        """Process raw audio data via processor.process_audio_data.

        Args:
            data (np.ndarray): Raw audio data returned from preprocessor.read_audio_data

        Returns:
            list: data processed to be analyzed
        """
        return self.processor.process_audio_data(data)

    def read_audio_data(self):
        """Read audio data from file and pass it on for preprocessing.

        Returns:
            _type_: _description_
        """
        rawdata = self.processor.read_audio_data(self.path)

        return self.process_audio_data(rawdata)
