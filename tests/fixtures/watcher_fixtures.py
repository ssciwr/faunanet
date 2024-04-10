import pytest
from pathlib import Path
import shutil
import time
import yaml
from datetime import datetime


def mock_recorder(number: int = 5):

    i = 0
    while i < 20:

        time.sleep(4)  # add a dummy time to emulate recording time

        print("copying")
        shutil.copy(
            Path("/home/hmack/iSparrow/example/soundscape.wav"),
            Path(f"/home/hmack/iSparrow_data/example_{i}.wav"),
        )

        i += 1


class WatchFixture:

    def __init__(self):
        self.filepath = Path(__file__).resolve()
        self.testpath = self.filepath.parent.parent
        cfgpath = (
            self.filepath.parent.parent.parent
            / Path("config")
            / Path("install_cfg.yml")
        )

        with open(cfgpath, "r") as file:
            cfg = yaml.safe_load(file)
            cfg = cfg["Directories"]

        self.sparrow_folder = Path(cfg["home"]).expanduser()
        self.models_folder = self.sparrow_folder / "models"

        with open(self.testpath / Path("test_configs") / "cfg_custom.yml", "r") as file:
            self.custom_cfg = yaml.safe_load(file)

        with open(
            self.testpath / Path("test_configs") / "cfg_default.yml", "r"
        ) as file:
            self.default_cfg = yaml.safe_load(file)

        with open(
            self.testpath / Path("test_configs") / "cfg_wrong_model.yml", "r"
        ) as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        self.preprocessor_cfg = {
            "sample_rate": 48000,
            "overlap": 0.0,
            "sample_secs": 3.0,
            "resample_type": "kaiser_fast",
        }

        self.model_cfg = {
            "num_threads": 1,
            "sigmoid_sensitivity": 1.0,
            "species_list_file": None,
        }

        self.recording_cfg = {
            "date": datetime(year=2022, month=5, day=10),
            "lat": 35.4244,
            "lon": -120.7463,
            "species_presence_threshold": 0.03,
            "min_conf": 0.25,
            "species_predictor": None,
        }

        self.recording_cfg_unrestricted = {
            "species_presence_threshold": 0.03,
            "min_conf": 0.25,
            "species_predictor": None,
        }

        self.species_predictor_cfg = {
            "use_cache": True,
            "num_threads": 1,
        }

        self.custom_preprocessor_cfg = {
            "sample_rate": 48000,
            "overlap": 0.0,
            "sample_secs": 3.0,
            "resample_type": "kaiser_fast",
        }

        self.custom_model_cfg = {
            "num_threads": 1,
            "sigmoid_sensitivity": 1.0,
            "default_model_path": str(Path.home() / "iSparrow/models/birdnet_default"),
        }


@pytest.fixture(scope="module")
def watch_fx():
    return WatchFixture()
