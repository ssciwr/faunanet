import pytest
from pathlib import Path
import shutil
import time
from datetime import datetime
from iSparrow.utils import wait_for_file_completion
from iSparrow import SparrowWatcher
from iSparrow import set_up as sus
from copy import deepcopy


class WatchFixture:

    def __init__(self):

        self.home = Path(sus.HOME)
        self.data = Path(sus.DATA)
        self.output = Path(sus.OUTPUT)

        self.data.mkdir(parents=True, exist_ok=True)
        self.output.mkdir(parents=True, exist_ok=True)

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

        self.changed_custom_model_cfg = {
            "num_threads": 1,
            "sigmoid_sensitivity": 0.8,  # change for testing
            "default_model_path": str(self.home / "models/birdnet_default"),
        }

        self.changed_custom_recording_cfg = {
            "species_presence_threshold": 0.03,
            "min_conf": 0.35,
        }

        self.path_add = Path(datetime.now().strftime("%y%m%d_%H%M%S"))

        # don't change the model config itself
        model_cfg2 = deepcopy(self.model_cfg)

        model_cfg2["name"] = "birdnet_default"

        self.config_should = {
            "Analysis": {
                "input": str(self.data),
                "output": str(self.output / self.path_add),
                "model_dir": str(self.home / "models"),
                "Preprocessor": deepcopy(self.preprocessor_cfg),
                "Model": model_cfg2,
                "Recording": deepcopy(self.recording_cfg),
                "SpeciesPredictor": deepcopy(self.species_predictor_cfg),
            }
        }

    def mock_recorder(self, home: str, data: str, number=10, sleep_for=4):

        for i in range(0, number, 1):

            time.sleep(sleep_for)  # add a dummy time to emulate recording time

            shutil.copy(
                Path(home) / Path("example/soundscape.wav"),
                Path(data) / Path(f"example_{i}.wav"),
            )

            wait_for_file_completion(Path(data) / Path(f"example_{i}.wav"))

    def make_watcher(self, **kwargs):
        return SparrowWatcher(
            self.data,
            self.output,
            self.home / "models",
            "birdnet_default",
            preprocessor_config=deepcopy(self.preprocessor_cfg),
            model_config=deepcopy(self.model_cfg),
            recording_config=deepcopy(self.recording_cfg),
            species_predictor_config=deepcopy(self.species_predictor_cfg),
            **kwargs,
        )

    def delete(self):
        for f in self.data.iterdir():
            if f.is_dir():
                shutil.rmtree(f)
            elif str(f)[0] == ".":
                continue
            else:
                f.unlink()

        for f in self.output.iterdir():
            shutil.rmtree(f)

    def get_folder_content(self, folder: str, pattern: str):
        files = [f for f in Path(folder).iterdir() if f.suffix == pattern]
        files.sort()
        return files

    def read_missings(self, watcher):
        missings = []
        with open(Path(watcher.output) / "missing_files.txt", "r") as mfile:
            for line in mfile:
                if line not in ["\n", "\0"]:
                    missings.append(line.strip("\n"))
        missings.sort()
        return missings

    def wait_for_event_then_do(
        self, condition: callable, todo_event: callable, todo_else: callable
    ):
        while True:
            if condition():
                todo_event()
                break
            else:
                todo_else()

    def delete_in_output(self, watcher, files: list):
        for f in files:
            for out in watcher.used_output_folders:
                if (out / f).exists():
                    (out / f).unlink()

    def delete_in_input(self, watcher, files: list):
        for f in files:
            if (watcher.input / f).exists():
                (watcher.input / f).unlink()


@pytest.fixture()
def watch_fx():
    w = WatchFixture()
    w.delete()
    return w
