import os
import numpy as np
from pathlib import Path
import datetime
import warnings

from birdnetlib.main import RecordingBase
from faunanet.preprocessor_base import PreprocessorBase
from faunanet.model_base import ModelBase
import faunanet.utils as utils
from faunanet.species_predictor import SpeciesPredictorBase


class Recording(RecordingBase):
    """
    Recording A Recording represents an audio recoding of arbitrary length and date associated with a preprocessor and analyzer object.

    Recordings read and preprocess audio data using the supplied preprocessor object and can use the 'analyzer' object to analyze and classify the contained animal sounds

    Args:
        RecordingBase (birdnetlib.RecordingBase): See documentation of the birdnetlib.RecordingBase class
    """

    def _check_model_system_viability(self, names_of_objects: list):

        # README: 'week' argument is not used because it doubles with 'date', and daily timestamps are more useful for data collection in general
        if all(name == names_of_objects[0] for name in names_of_objects) is False:

            raise ValueError(
                "Found different 'name' attributes for model, preprocessor and species predictor. Make sure the supplied model, preprocessor and species predictor are compatible to each other (species_predictor may be 'None' if not used)."
            )

    def __init__(
        self,
        preprocessor: PreprocessorBase,
        model: ModelBase,
        path: str,
        date: datetime.datetime = None,
        lat: float = None,
        lon: float = None,
        species_presence_threshold: float = 0.03,
        min_conf: float = 0.25,
        species_predictor: SpeciesPredictorBase = None,
        file_check_poll_interval: int = 1,
    ):
        # README: The arguments lon, lat, species_presence_threshold and week_48, date should be moved out of the __init__ at some point, at some point perhaps?
        """
        Create a new Recording.

        Args:
            analyzer (Analyzer): Analyzer object to use. Contains model to use for analysis as well as result post processing.
            preprocessor (PreprocessorBase): Preprocessor object to use. Must adhere to the interface defined in faunanet.preprocessor_base.
            path (str): Path to the audio file to be analyzed
            date (datetime, optional): Date of recording. Alternative to 'week'. Defaults to None. Only applied if `model` is the birdnet default model.
            sensitivity (float, optional): Detection sensitivity. Defaults to 1.0.
            lat (float, optional): Latitude. If latitude and longitude are given, the species list is predicted first.  Defaults to None. Only applied if `model` is the birdnet default model.
            lon (float, optional): Longitude. If latitude and longitude are given, the species list is predicted first.  Defaults to None. Only applied if `model` is the birdnet default model.
            species_presence_threshold (float, optional): The threshold for the species predictor. A species predicted to be present above that threshold is added to the list of allowed species, below it is excluded. Restricted to [0,1]
            min_conf (float, optional): Minimal confidence to use to consider a detection valid. Defaults to 0.1.
            species_predictor: An instance of a class derived from `SpeciesPredictorBase`. Only applicable if `model` is the birdnet default model.
            file_check_poll_interval: Inteval in seconds at which the recording should check whether the file to be analyzed is still being written to. Defaults to 1
        """
        self.processor = preprocessor
        self.analyzer = model
        self.path = path
        p = Path(self.path)
        self.filestem = p.stem
        self.species_predictor = None
        self.allowed_species = []
        self.file_check_poll_interval = file_check_poll_interval

        # make sure that all the system components are compatible. Based on name tags. Still a bit susceptible. Fix?

        self._check_model_system_viability(
            [
                model.name,
                preprocessor.name,
                model.name if species_predictor is None else species_predictor.name,
            ]
        )

        species_predictor_args = [lat, lon, species_predictor, date]

        # check that necessary info is present for species predictor: nothing necessary is None and a date variable is given
        if all(var is not None for var in species_predictor_args):

            self.species_predictor = species_predictor

            self.allowed_species = self.species_predictor.predict(
                latitude=lat,
                longitude=lon,
                date=date,
                threshold=species_presence_threshold,
            )

        # when any of the species predictor stuff is None and something else is not,
        # we have an incompatible combination.
        if any(var is None for var in species_predictor_args) and any(
            var is not None for var in species_predictor_args
        ):
            raise ValueError(
                "A full set of (lat, lon, date/week_48) must be given to use the species presence predictor and the passed species predictor must not be 'None'."
            )

        # README: can we get rid of the birdnetlib-Recording thing completely at some point?

        # we ignore the underlying species predictor stuff that the birdnetlib base class does
        # by not passing it the respective arguments.
        super().__init__(
            model,
            sensitivity=1.0,
            min_conf=min_conf,
            overlap=0.0,
            return_all_detections=False,  # not used in faunanet. Set min_conf to 0 for the same effect
        )

    @property
    def filename(self):
        return os.path.basename(self.path)

    @property
    def chunks(self):
        return self.processor.chunks

    def set_analyzer(
        self,
        model: ModelBase,
        preprocessor: PreprocessorBase,
        species_predictor: SpeciesPredictorBase = None,
    ):
        """
        set_analyzer Replace the internally used model and preprocessor.

        Args:
            model (ModelBase): The classifier model to use
            preprocessor (PreprocessorBase): The preprocessor to use
        """

        self._check_model_system_viability(
            [
                model.name,
                preprocessor.name,
                model.name if species_predictor is None else species_predictor.name,
            ]
        )

        self.analyzer = model

        self.processor = preprocessor

        if species_predictor is not None:
            self.species_predictor = species_predictor

        self.analyzed = False

    def restrict_species_list(
        self,
        lat: float,
        lon: float,
        date: datetime.datetime = None,
        species_presence_threshold: float = 0.03,
    ):
        # this abstracts away the underlying species predictor model and is useful when reusing the recording or
        # into whatever class it may morph in the future.
        """
        restrict_species_list Restrict the list of possibly present species based on coordinates and time.

        Args:
            lat (float): Latitude coordinate to predict species presence for.
            lon (float): Longitude coordinate to predict species presence for.
            date (datetime, optional): Date to predict species presence for. Only relevant when 'week' is not -1. Defaults to None.
            week (int, optional): Week (4 weeks per month) to predict species presence for. Defaults to -1. Only relevant when 'date' is None.
            species_presence_threshold (float, optional): Threshold above which a species is considered to be persent. Restricted to [0, 1]. Defaults to 0.03.
        """
        self.allowed_species = self.species_predictor.predict(
            latitude=lat,
            longitude=lon,
            date=date,
            threshold=species_presence_threshold,
        )

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
            list[np.array]: preprocessed audio data
        """

        # README: wait until the file to be opened does not change in size anymore.
        # only working way in which we do not have to make assumptions about the
        # system that actually writes the file?
        utils.wait_for_file_completion(
            str(self.path), polling_interval=self.file_check_poll_interval
        )

        rawdata = self.processor.read_audio_data(self.path)

        return self.process_audio_data(rawdata)

    @classmethod
    def from_cfg(cls, faunanet_path: str, cfg: dict):
        """
        from_cfg Create a new Recording from a dictionary containing all keyword arguments. Usually, this is obtained by reading in a YAML config.

        Args:
            faunanet_path (str): Path to the faunanet installation
            cfg (dict): keyword arguments for the Recording and its 'preprocessor' and 'model' attributes.

        Returns:
            Recording: New instance build with supplied kwargs.
        """
        # README: faunanet path needed still -> can we get rid of it in some way?
        # config.py/.yml written upon install or something....
        # future PR when installing/packaging is done

        # load appropriate modules: preprocessor, model

        module_path = Path(faunanet_path) / Path("models") / cfg["Model"]["model_path"]

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
        """
        detections Produce a list of tuples containting (start_time, end_time, label, detection_confidence) from the raw detections produced by the 'model' attribute of this class.
        Also filters them by minimum confidence level.

        Returns:
            List(Tuples): A list containing a tuple (start, end, lable, confidence) for each detection with confidence > self.minimum_confidence.
        """
        # Readme: overrides the detections method of the base class to make things a bit simpler and remove stuff
        # that is currently not supported here or which is too specific.

        if not self.analyzed:
            warnings.warn(
                "'analyze' method has not been called. Call .analyze() before accessing detections.",
                RuntimeWarning,
            )

        qualified_detections = []

        allow_list = set(
            self.allowed_species
        )  # convert to set for lookup speed. Useful? (maybe for bigger lists...)

        for (start, end), labeled_predictions in self.analyzer.results.items():

            for label, confidence in labeled_predictions:
                if confidence > self.minimum_confidence:
                    if label in allow_list or len(allow_list) == 0:

                        qualified_detections.append(
                            {
                                "start": start,
                                "end": end,
                                "label": label,
                                "confidence": confidence,
                            }
                        )

        return qualified_detections
