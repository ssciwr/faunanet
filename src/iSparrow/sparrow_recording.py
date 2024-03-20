import os
import numpy as np
from pathlib import Path
import datetime
from birdnetlib.main import RecordingBase
from .preprocessor_base import PreprocessorBase
from .sparrow_model_base import ModelBase
from . import utils
import warnings


class SparrowRecording(RecordingBase):
    """
    SparrowRecording A SparrowRecording represents an audio recoding of arbitrary length and date associated with a preprocessor and analyzer object.

    SparrowRecordings read and preprocess audio data using the supplied preprocessor object and can use the 'analyzer' object to analyze and classify the contained animal sounds

    Args:
        RecordingBase (birdnetlib.RecordingBase): See documentation of the birdnetlib.RecordingBase class
    """

    def __init__(
        self,
        preprocessor: PreprocessorBase,
        model: ModelBase,
        path: str,
        week_48: int = -1,
        date: datetime = None,
        lat: float = None,
        lon: float = None,
        return_all_detections: bool = False,
        min_conf: float = 0.25,
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
        self.model = model
        self.path = path
        p = Path(self.path)
        self.filestem = p.stem

        # TODO: can we get rid of the analyzer thing completely?
        super().__init__(
            model,
            week_48=week_48,
            date=date,
            sensitivity=1.0,
            lat=lat,
            lon=lon,
            min_conf=min_conf,
            overlap=0.0,
            return_all_detections=return_all_detections,
        )

    @property
    def filename(self):
        return os.path.basename(self.path)

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

    @classmethod
    def from_cfg(cls, sparrow_path: str, cfg: dict):
        # README: sparrow path needed still -> can we get rid of it in some way?
        # config.py/.yml written upon install or something....
        # future PR when installing/packaging is done

        # load appropriate modules: preprocessor, model

        module_path = Path(sparrow_path) / Path("models") / cfg["Model"]["model_path"]

        preproc_m = utils.load_module("pp", str(module_path / "preprocessor.py"))

        model_m = utils.load_module("mm", str(module_path / "model.py"))

        # make preprocessor instance
        preprocessor = preproc_m.Preprocessor.from_cfg(cfg["Data"]["Preprocessor"])

        # make model instance
        model = model_m.Model.from_cfg(cfg["Analysis"]["Model"])

        # make recording instance and return

        defaults = {
            "path": None,
            "week_48": -1,
            "date": None,
            "lat": None,
            "lon": None,
            "return_all_detections": False,
            "min_conf": 0.25,
        }

        del cfg["Analysis"]["Model"]

        return cls(preprocessor, model, **(defaults | cfg["Analysis"]))

    @property
    def detections(self):
        # overrides the detections method of the base class to make things a bit simpler and remove stuff
        # that is currently not supported here.

        if not self.analyzed:
            warnings.warn(
                "'analyze' method has not been called. Call .analyze() before accessing detections.",
                RuntimeWarning,
            )

        qualified_detections = []

        # allow_list = self.analyzer.custom_species_list
        for (start, end), labeled_predictions in self.model.results.items():

            # README: this needs to include allowed species later
            for label, confidence in labeled_predictions:
                if confidence > self.minimum_confidence:
                    qualified_detections.append(
                        {
                            "start": start,
                            "end": end,
                            "label": label,
                            "confidence": confidence,
                        }
                    )

        return qualified_detections
