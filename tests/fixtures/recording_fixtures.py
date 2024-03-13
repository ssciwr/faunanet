import pytest
from pathlib import Path
import importlib
import yaml
import sys
import pandas as pd

sys.path.append("../src/iSparrow")

from src.iSparrow import sparrow_analyzer as spa
from src.iSparrow import sparrow_recording as spc


class RecordingFixture:
    """Provides data to execute recording tests"""

    def __init__(self):
        self.sparrow_folder = Path.home() / Path("iSparrow")

        self.data_path = self.sparrow_folder / Path("data")

        with open(self.data_path / "cfg.yml", "r") as file:
            self.cfg = yaml.safe_load(file)

        with open(self.data_path / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        # import preprocessor definition that we need
        pp = importlib.import_module(
            "models." + self.cfg["Analyzer"]["Model"]["model_name"] + ".preprocessor"
        )

        ppd = importlib.import_module(
            "models." + "birdnet_defaults" + ".preprocessor"
        )

        self.preprocessor = pp.preprocessor_from_config(
            self.cfg["Data"]["Preprocessor"]
        )

        self.analyzer = spa.analyzer_from_config(str(self.sparrow_folder), self.cfg["Analyzer"])

        self.default_analyzer = spa.analyzer_from_config(str(self.sparrow_folder), self.default_cfg["Analyzer"])
        
        self.default_preprocessor = ppd.preprocessor_from_config(self.default_cfg["Data"]["Preprocessor"])

        self.good_file = self.data_path / "soundscape.wav"

        self.corrupted_file = self.data_path / "corrupted.wav"

        self.trimmed_file = self.data_path / "trimmed.wav"

        self.custom_analysis_results = pd.read_csv(
            self.data_path / Path("custom_results.csv")
        )

        self.default_analysis_results = pd.read_csv(
            self.data_path / Path("default_results.csv")
        )


@pytest.fixture
def recording_fx():

    return RecordingFixture()
