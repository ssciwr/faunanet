import pytest
from pathlib import Path
import shutil
import time
import yaml
from datetime import datetime
from iSparrow.utils import wait_for_file_completion
from iSparrow import SparrowWatcher
from .. import set_up_sparrow_env
from copy import deepcopy


class WatchFixture:

    def __init__(self):
        filepath = Path(__file__).resolve()
        self.testpath = filepath.parent.parent
        cfgpath = (
            filepath.parent.parent.parent / Path("config") / Path("install_cfg.yml")
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
            "date": datetime(year=2024, month=1, day=24),
            "lat": 42.5,
            "lon": -76.45,
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

        self.home = set_up_sparrow_env.HOME
        self.data = set_up_sparrow_env.DATA
        self.output = set_up_sparrow_env.OUTPUT

    def mock_recorder(self, home: str, data: str, number=10, sleep_for=4):
        for i in range(0, number, 1):

            time.sleep(sleep_for)  # add a dummy time to emulate recording time

            shutil.copy(
                Path(home) / Path("example/soundscape.wav"),
                Path(data) / Path(f"example_{i}.wav"),
            )

            wait_for_file_completion(Path(data) / Path(f"example_{i}.wav"))

    def standard_watcher(self):
        return SparrowWatcher(
            self.data,
            self.output,
            self.home / "models",
            "birdnet_default",
            preprocessor_config=self.preprocessor_cfg,
            model_config=self.model_cfg,
            recording_config=deepcopy(self.recording_cfg),
            species_predictor_config=self.species_predictor_cfg,
        )

    def delete(self):
        for f in self.data.iterdir():
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()

        for f in self.output.iterdir():
            shutil.rmtree(f)


@pytest.fixture()
def watch_fx():
    w = WatchFixture()
    w.delete()
    return w
