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
        latitude: float,
        longitude: float,
        week_48: int = None,
        date: datetime = None,
        use_cache: bool = True,
        from_file_only: bool = False,
        threshold: float = 0.0,
        num_threads: int = 1,
    ):
        self.model_path = Path(model_path) / "species_range_model.tflite"

        self.labels_path = Path(model_path) / "labels.txt"

        self.use_cache = use_cache

        self.num_threads = num_threads

        self.results = []

        if week_48 is not None and date is not None:
            warnings.warn(
                "Both `week` and `date` have been set, using `date` and ignoring `week`"
            )

        # have plattform independent cache for the lists
        self.cache_dir = user_cache_dir()

        super.__init__()

    def load_species_list_model(self):
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
        # README: this assumes there is only one label per line and nothing else.
        self.labels = self._read_labels_file(self.labels_path)

    def predict_species_list(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date = None,
        week: int = -1,  # default from birdnetlib.required for their remapping logic to the format neede by birdnet analyzer. Why?
        threshold: float = 0.3,
    ):
        """
        predict_species_list Apply the model for species presence prediction at (longitude, latitude) coordinates at date 'date' (will be converted to a week) or within a given week. Override this in a derived  class if you want to customize how species presence is restricted.

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
            threshold=threshold,
        )

    def predict(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date = None,
        week: int = None,
        threshold: float = 0.3,
    ):

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
            self.predict(
                latitude=latitude,
                longitude=longitude,
                week=week,
                date=date,
                threshold=threshold,
            )

            detections = self.detections

            if self.use_cache:  # store when requested
                self._write_to_cache(
                    detections,
                    Path(self.cache_dir)
                    / Path("iSparrow")
                    / Path(str(self.latitude) + "_" + str(self.longitude)),
                )

            return detections

    @property
    def detections(self) -> list:
        """
        detections Turn raw species presences prediction results into the labels format used by the model. Override this method in a derived class to get custom formats.

        Returns:
            list: Predicted species in the format needed by the model
        """
        # transform the species list into the birdnet format.
        return [
            "{scientific_name}_{common_name}"
            for scientific_name, common_name, _ in self.results
        ]

    def _read_labels_file(self, filepath: Path) -> list:
        with open(filepath, "r") as lfile:
            read_data = [line.replace("\n", "") for line in lfile.readlines()]
        return read_data

    def _write_to_cache(self, containing_folder: Path, formatted_results: list):
        dir = containing_folder.mkdir(parents=True, exist_ok=True)

        with open(dir / "species_list.txt", "w") as output:
            writer = csv.writer(output)
            writer.writerows(formatted_results)
