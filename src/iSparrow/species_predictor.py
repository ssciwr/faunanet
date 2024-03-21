from appdirs import user_cache_dir
from pathlib import Path
import csv
import datetime
from birdnetlib.species import SpeciesList
from birdnetlib.utils import return_week_48_from_datetime

import warnings
from . import utils

# README: Would be more logically consistent to have this inherit from Sparrow's `ModelBase` class,
# but that would require a lot of copy-cat code from birdnetlib.


class SpeciesPredictorBase(SpeciesList):

    def __init__(
        self,
        model_path: str,
        use_cache: bool = True,
        threshold: float = 0.0,
        num_threads: int = 1,
    ):
        """
        __init__ Create a new SpeciesPredictorBase instance.

        Args:
            model_path (str): _description_
            use_cache (bool, optional): _description_. Defaults to True.
            num_threads (int, optional): _description_. Defaults to 1.
        """

        if (Path(model_path) / "species_presence_model.tflite").exists() is False:
            raise FileNotFoundError(
                "The 'model' file for the species presence predictor could not be found."
            )

        self.model_path = str(Path(model_path) / "species_presence_model.tflite")

        if (Path(model_path) / "labels.txt").exists() is False:
            raise FileNotFoundError(
                "The 'labels' file for the species presence predictor could not be found."
            )

        self.labels_path = str(Path(model_path) / "labels.txt")

        self.use_cache = use_cache

        self.num_threads = num_threads

        self.threshold = threshold

        self.results = []

        # have plattform independent cache for the produced species list
        self.cache_dir = user_cache_dir()

        super.__init__()  # super class handles model loadin

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
        self.meta_output_layer_ind

    def load_labels(self):
        """
        load_species_list_model Load the full species labels list used by the prediction model that should be restricted.
        """
        # README: this assumes there is only one label per line and nothing else.
        self.labels = self._read_labels_file(self.labels_path)

    def predict_species_list(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date = None,
        week: int = -1,  # default from birdnetlib.required for their remapping logic to the format neede by birdnet analyzer. Why?
    ):
        """
        predict_species_list Apply the model for species presence prediction at (longitude, latitude) coordinates at date 'date' (will be converted to a week) or within a given week, using a confidence threshold to mark species as present. Override this in a derived  class if you want to customize how species presence is restricted.

        Args:
            latitude (float): Latitude value for location coordinate
            longitude (float): Longitude value for location coordinate
            date (datetime.date, optional): Date to restrict the species presence to. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to None.
            week (int, optional): Week to restrict the species presence. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to -1.
            threshold (float, optional): Detection threshold to mark a species as being present. Defaults to 0.3.
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
            week_48=week,
            threshold=self.threshold,
        )

    def predict(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date = None,
        week: int = -1,
    ) -> list:
        """
        predict Predict the presence of species in the original label set using coordinates (latitude, longitude) and a timestep (week within a year), using a supplied threshold to set a confidence limit to mark a species as present. if `use_cache` is true in the caller, attempts to use a cached species list instead of computing a new one.
        Otherwise, the arguments are passed internally to the 'predict_species_list' function which then creates a new list. Override in a derived class to customize behavior.
        Args:
            latitude (float): Latitude value for location coordinate
            longitude (float): Longitude value for location coordinate
            date (datetime.date, optional): Date to restrict the species presence to. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to None.
            week (int, optional): Week to restrict the species presence. If both 'week' and 'date' are present, the week will be computed from the date. Defaults to -1.
            threshold (float, optional): Detection threshold to mark a species as being present. Defaults to 0.3.

        Raises:
            ValueError: When week and date are both None. One of both needs to be present.

        Returns:
            list: List of label names according to the formatting applied in the 'detections' function.
        """
        if week is None and date is None:
            raise ValueError(
                "Either week or date must be given for species list prediction"
            )

        if week is not None and date is not None:
            warnings.warn(
                "Both date and week given for species list prediction. Using date to determine week."
            )

        if date is not None:

            week = return_week_48_from_datetime(
                date
            )  # not optimal, this is called in ´return_results' again.

        # when we want to use cached results, we first check if we computed a list for this location and date before
        if self.use_cache and (
            Path(str(latitude) + "_" + str(longitude) + "_" + str(week))
            in Path(self.cache_dir).iterdir()
        ):
            return self._read_labels_file(
                Path(self.cache_dir)
                / Path(str(latitude) + "_" + str(longitude) + "_" + str(week))
                / "species_list.txt"
            )

        else:

            # provides raw species presence data in self.result
            self.predict(latitude=latitude, longitude=longitude, week=week, date=date)

            detections = self.detections

            if self.use_cache:  # store when requested. Round given coords to 2 decimals
                self._write_to_file(
                    detections,
                    Path(self.cache_dir)
                    / Path("iSparrow")
                    / Path(
                        str(round(self.latitude, 2))
                        + "_"
                        + str(round(self.longitude, 2))
                    ),
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
        return [
            "{scientific_name}_{common_name}"
            for scientific_name, common_name, _ in self.results
        ]

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

        self._write_to_file(Path(outpath, self.detections))

    def _read_labels_file(self, filepath: Path) -> list:
        """
        _read_labels_file Reads labels.txt file. Only single-column files are supported.

        """
        with open(filepath, "r") as lfile:
            read_data = [line.replace("\n", "") for line in lfile.readlines()]

        return read_data

    def _write_to_file(self, containing_folder: Path, formatted_results: list):
        """Write produced species list to 'containing_folder' within the cache_dir path held by the caller. Creates directories as necessary"""

        dir = containing_folder.mkdir(parents=True, exist_ok=True)

        with open(dir / "species_list.txt", "w") as output:
            writer = csv.writer(output)
            writer.writerows(formatted_results)
