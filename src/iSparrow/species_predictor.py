from appdirs import user_cache_dir
from pathlib import Path
import datetime
from birdnetlib.species import SpeciesList
from birdnetlib.utils import return_week_48_from_datetime
from shutil import rmtree
import warnings
from . import utils

# README: Would be more logically consistent to have this inherit from Sparrow's `ModelBase` class,
# but that would require a lot of copy-cat code from birdnetlib.


class SpeciesPredictorBase(SpeciesList):

    # make this a class attribute since it´s the same always
    cache_dir = user_cache_dir() / Path("iSparrow") / Path("species_lists")

    def __init__(
        self,
        model_path: str,
        use_cache: bool = True,
        num_threads: int = 1,
    ):
        """
        __init__ Create a new SpeciesPredictorBase instance.

        Args:
            model_path (str): _description_
            use_cache (bool, optional): _description_. Defaults to True.
            num_threads (int, optional): _description_. Defaults to 1.
        """

        if Path(model_path).exists() is False:
            raise FileNotFoundError(
                "The model folder for the species presenece predictor could not be found"
            )

        labels_path = Path(model_path) / "labels.txt"

        if labels_path.exists() is False:
            raise FileNotFoundError(
                "The 'labels' file for the species presence predictor could not be found"
            )

        model_path = Path(model_path) / "species_presence_model.tflite"

        if model_path.exists() is False:
            raise FileNotFoundError(
                "The 'model' file for the species presence predictor could not be found"
            )

        self.model_path = str(model_path)

        self.labels_path = str(labels_path)

        self.use_cache = use_cache

        self.num_threads = num_threads

        self.results = []

        self.read_from_file = False  # variable used for debugging mostly

        self.name = "birdnet_default"

        if SpeciesPredictorBase.cache_dir.exists() is False:
            SpeciesPredictorBase.cache_dir.mkdir(parents=True, exist_ok=True)

        super().__init__()  # super class handles model loading

    def load_species_list_model(self):
        """
        load_species_list_model Load the default species presence model used by Birdnet-Analyzer.
        """
        self.meta_interpreter = utils.load_model_from_file_tflite(
            self.model_path, self.num_threads
        )
        self.meta_interpreter.allocate_tensors()
        # Get input and output tensors.
        self.meta_input_details = self.meta_interpreter.get_input_details()
        self.meta_output_details = self.meta_interpreter.get_output_details()

        # Get input tensor index
        self.meta_input_layer_index = self.meta_input_details[0]["index"]
        self.meta_output_layer_index = self.meta_output_details[0]["index"]

    def load_labels(self):
        """
        load_species_list_model Load the full species labels list used by the prediction model that should be restricted.
        """
        # README: this assumes there is only one label per line and nothing else -> fix by using pandas?
        self.labels = self._read_labels_file(self.labels_path)

    def predict_species_list(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date = None,
        threshold: float = 0.03,
    ):
        """
        predict_species_list Apply the model for species presence prediction at (longitude, latitude) coordinates at date 'date' (will be converted to a week) or within a given week, using a confidence threshold to mark species as present. Override this in a derived  class if you want to customize how species presence is restricted.

        Args:
            latitude (float): Latitude value for location coordinate
            longitude (float): Longitude value for location coordinate
            date (datetime.date, optional): Date to restrict the species presence to. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to None.
            threshold (float, optional): Detection threshold to mark a species as being present. Defaults to 0.03.
        """
        self.results = []

        # this relies on the birdnetlib format and returns [{
        #     "scientific_name": sc,
        #     "common_name": cn,
        #     "threshold": t,
        # }, {"scientific_name: " sc, ...}, { ... }]

        self.results = self.return_list(
            lon=longitude,
            lat=latitude,
            date=date,
            threshold=threshold,
        )

    # README: coordinates are not members becaues this is intended to be used from within another class that holds those
    def predict(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date = None,
        threshold: float = 0.03,
    ) -> list:
        """
        predict Predict the presence of species in the original label set using coordinates (latitude, longitude) and a timestep (week within a year), using a supplied threshold to set a confidence limit to mark a species as present. if `use_cache` is true in the caller, attempts to use a cached species list instead of computing a new one.
        Otherwise, the arguments are passed internally to the 'predict_species_list' function which then creates a new list. Override in a derived class to customize behavior.
        Args:
            latitude (float): Latitude value for location coordinate
            longitude (float): Longitude value for location coordinate
            date (datetime.date, optional): Date to restrict the species presence to. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to None.
            week (int, optional): Week to restrict the species presence. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to -1.
            threshold (float, optional): Detection threshold to mark a species as being present. Defaults to 0.03.

        Raises:
            ValueError: When week and date are both None. One of both needs to be present.

        Returns:
            list: List of label names according to the formatting applied in the 'detections' function.
        """

        self.read_from_file = False

        if date is not None:

            week = return_week_48_from_datetime(
                date
            )  # not optimal, this is called in ´return_results' again.

        # when we want to use cached results, we first check if we computed a list for this location and date before
        cache_folder = Path(str(latitude) + "_" + str(longitude) + "_" + str(week))

        if self.use_cache:

            if (
                SpeciesPredictorBase.cache_dir / cache_folder / "species_list.txt"
            ).exists():
                self.read_from_file = True

                return self._read_labels_file(
                    Path(SpeciesPredictorBase.cache_dir)
                    / cache_folder
                    / "species_list.txt"
                )

        # provides raw species presence data in self.result
        self.predict_species_list(
            latitude=latitude,
            longitude=longitude,
            date=date,
            threshold=threshold,
        )

        detections = self.detections

        if self.use_cache:  # store when requested. Round given coords to 2 decimals

            self._write_to_file(
                Path(SpeciesPredictorBase.cache_dir) / cache_folder,
                detections,
            )

        return detections

    @property
    def detections(self) -> list:
        """
        detections Turn raw species presences prediction results into the labels format used by the model. Override this method in a derived class to get custom formats for different models

        Returns:
            list: Predicted species in the format needed by the model
        """
        # transform the species list into the birdnet format.

        detections = []
        for dictionary in self.results:
            sn = dictionary["scientific_name"]
            cn = dictionary["common_name"]

            detections.append(f"{sn}_{cn}")

        return detections

    def export(self, outpath: str):
        """
        export Export a generated species list to file residing at 'outputpath'

        Args:
            outpath (str): absolute path to the output file.

        Raises:
            RuntimeError: When there is no stored specieslist to write to file.
        """
        if len(self.results) == 0:
            raise RuntimeError(
                "No results present, first generate a species list by calling 'predict'"
            )

        self._write_to_file(Path(outpath), self.detections)

    def _read_labels_file(self, filepath: Path) -> list:
        """
        _read_labels_file Reads labels.txt file. Only single-column files are supported.

        """
        with open(filepath, "r") as lfile:
            read_data = [line.replace("\n", "") for line in lfile.readlines()]

        return read_data

    def _write_to_file(self, containing_folder: Path, formatted_results: list):
        """Write produced species list to 'containing_folder' within the cache_dir path held by the caller. Creates directories as necessary"""

        containing_folder.mkdir(parents=True, exist_ok=True)

        with open(containing_folder / "species_list.txt", "w") as output:
            for row in formatted_results:
                output.write(row + "\n")

    @classmethod
    def clear_cache(
        cls,
    ):
        """
        clear_cache Remove the cache folder completely

        """
        if cls.cache_dir.exists():
            rmtree(str(cls.cache_dir))
