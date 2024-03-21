from . import sparrow_model_base as smb
from appdirs import user_cache_dir
from pathlib import Path
import csv
import datetime


class SpeciesPredictor(smb.ModelBase):

    def __init__(
        self,
        model_path: str,
        latitude: float,
        longitude: float,
        week: int,
        date: datetime = None,
        use_cache: bool = True,
        from_file_only: bool = False,
    ):
        self.model_path = model_path

        self.labels_path = None

        self.latitude = latitude

        self.longitude = longitude

        self.use_cache = use_cache

        # have plattform independent cache for the lists
        self.cache_dir = user_cache_dir()

    def load_model(self):
        pass

    def load_labels(self):
        pass

    def predict(self):

        if self.use_cache and (
            Path(str(self.latitude) + "_" + str(self.longitude))
            in Path(self.cache_dir).iterdir()
        ):
            self.results = self._load_from_cache()

        else:
            self.results = []  # TODO: invoke the model and get out the results

            if self.use_cache:  # store when requested

                dir = (
                    Path(self.cache_dir)
                    / Path(str(self.latitude) + "_" + str(self.longitude))
                ).mkdir()

                with open(dir / "species_list.txt") as output:
                    writer = csv.writer(output)
                    writer.writerow(
                        [
                            "label",
                        ]
                    )
                    writer.writerows(self.results)

    def detections(self):
        pass

    def _load_from_cache(self):
        pass

    def _write_to_cache(self):
        pass
