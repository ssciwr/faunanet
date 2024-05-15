import pytest
from pathlib import Path
import shutil
import time
from datetime import datetime
from iSparrow.utils import wait_for_file_completion
from iSparrow import SparrowWatcher
from copy import deepcopy


class WatchFixture:

    def __init__(self, home: str, data: str, output: str, models: str):

        self.home = home
        self.data = data
        self.output = output
        self.models = models
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
            "default_model_path": str(self.models / "birdnet_default"),
        }

        self.changed_custom_model_cfg = {
            "num_threads": 1,
            "sigmoid_sensitivity": 0.8,  # change for testing
            "default_model_path": str(self.models / "birdnet_default"),
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
                "model_dir": str(self.models),
                "Preprocessor": deepcopy(self.preprocessor_cfg),
                "Model": model_cfg2,
                "Recording": deepcopy(self.recording_cfg),
                "SpeciesPredictor": deepcopy(self.species_predictor_cfg),
            }
        }

    # below are helper functions for the watcher test that are mainly there
    # to keep the test code clean and more readable and avoid repetition

    def mock_recorder(self, home: str, data: str, number=10, sleep_for=4):

        for i in range(0, number, 1):

            time.sleep(sleep_for)  # add a dummy time to emulate recording time

            shutil.copy(
                Path(home) / Path("example/soundscape.wav"),
                Path(data) / Path(f"example_{i}.wav"),
            )

            wait_for_file_completion(Path(data) / Path(f"example_{i}.wav"))

    def make_watcher(self, **kwargs):
        # README: the only reason this exists is because SonarCloud is complaining about code repetition
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

    def get_folder_content(self, folder: str, pattern: str):
        files = [f for f in Path(folder).iterdir() if f.suffix == pattern]
        files.sort()
        return files

    def wait_for_event_then_do(
        self,
        condition: callable,
        todo_event: callable,
        todo_else: callable,
        limit: int = 20,
    ):
        i = 0
        while True:
            if condition():
                todo_event()
                break
            elif i >= limit:
                raise TimeoutError("Timeout reached")
            else:
                todo_else()
                i += 1
