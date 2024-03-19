import sys

sys.path.append("../src/iSparrow")
from src.iSparrow import utils

from pathlib import Path
import yaml
import pytest
import pandas as pd


class ModelFixture:

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

        with open(self.testpath / "cfg_custom.yml", "r") as file:
            self.custom_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_wrong_model.yml", "r") as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        with open(self.testpath / "cfg_google.yml", "r") as file:
            self.google_cfg = yaml.safe_load(file)

        self.default_module = utils.load_module(
            "model_default",
            str(
                self.models_folder
                / Path(self.default_cfg["Analyzer"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.default_pp = utils.load_module(
            "pp_default",
            str(
                self.models_folder
                / Path(self.default_cfg["Analyzer"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        self.custom_module = utils.load_module(
            "model_custom",
            str(
                self.models_folder
                / Path(self.custom_cfg["Analyzer"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.google_module = utils.load_module(
            "model_google",
            str(
                self.models_folder
                / Path(self.google_cfg["Analyzer"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.google_pp = utils.load_module(
            "pp_google",
            str(
                self.models_folder
                / Path(self.google_cfg["Analyzer"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        ppd = self.default_pp.Preprocessor()

        data_default = ppd.read_audio_data(
            self.sparrow_folder / "example" / "soundscape.wav"
        )

        self.data_default = ppd.process_audio_data(data_default)

        ppg = self.google_pp.Preprocessor()

        data_google = ppg.read_audio_data(
            self.sparrow_folder / "example" / "soundscape.wav"
        )

        self.data_google = ppg.process_audio_data(data_google)

        # read data made with birdnet-Analyzer for cross checking
        self.default_analysis_results = (
            pd.read_csv(self.testpath / Path("default_results.csv"))
            .loc[:, ["scientific_name", "confidence"]]
            .sort_values(by="confidence", ascending=False)
        )

        self.custom_analysis_results = (
            pd.read_csv(self.testpath / Path("custom_results.csv"))
            .loc[:, ["scientific_name", "confidence"]]
            .sort_values(by="confidence", ascending=False)
        )


@pytest.fixture
def model_fx():
    return ModelFixture()