import pytest
from pathlib import Path
import yaml
import sys
import pandas as pd

sys.path.append("../src/iSparrow")

from src.iSparrow import sparrow_recording as spc
from src.iSparrow import utils


class RecordingFixture:
    """Provides data to execute recording tests"""

    def __init__(self):
        filepath = Path(__file__).resolve()
        self.testpath = filepath.parent.parent

        cfgpath = (
            filepath.parent.parent.parent / Path("config") / Path("install_cfg.yml")
        )
        with open(cfgpath, "r") as file:
            sparrow_cfg = yaml.safe_load(file)
            sparrow_cfg = sparrow_cfg["Directories"]

        self.sparrow_folder = Path(sparrow_cfg["home"]).expanduser()

        self.models_folder = self.sparrow_folder / "models"

        self.example_folder = self.sparrow_folder / "example"

        with open(self.testpath / "cfg_custom.yml", "r") as file:
            self.custom_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_google.yml", "r") as file:
            self.google_cfg = yaml.safe_load(file)
        # import preprocessor definition that we need

        pp = utils.load_module(
            "pp",
            str(
                self.models_folder
                / Path(self.custom_cfg["Analysis"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        ppd = utils.load_module(
            "ppd",
            str(
                self.models_folder
                / Path(self.default_cfg["Analysis"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        ppg = utils.load_module(
            "ppg",
            str(
                self.models_folder
                / Path(self.google_cfg["Analysis"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        cmm = utils.load_module(
            "cmm",
            str(
                self.models_folder
                / Path(self.custom_cfg["Analysis"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        dmm = utils.load_module(
            "dmm",
            str(
                self.models_folder
                / Path(self.default_cfg["Analysis"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        gmm = utils.load_module(
            "gmm",
            str(
                self.models_folder
                / Path(self.google_cfg["Analysis"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.custom_preprocessor = pp.Preprocessor.from_cfg(
            self.custom_cfg["Data"]["Preprocessor"]
        )

        self.default_preprocessor = ppd.Preprocessor.from_cfg(
            self.default_cfg["Data"]["Preprocessor"]
        )

        self.google_preprocessor = ppg.Preprocessor.from_cfg(
            self.google_cfg["Data"]["Preprocessor"]
        )

        self.custom_model = cmm.Model.from_cfg(
            self.sparrow_folder, self.custom_cfg["Analysis"]["Model"]
        )

        self.default_model = dmm.Model.from_cfg(
            self.sparrow_folder, self.default_cfg["Analysis"]["Model"]
        )

        self.google_model = gmm.Model.from_cfg(
            self.sparrow_folder, self.google_cfg["Analysis"]["Model"]
        )

        self.good_file = self.example_folder / "soundscape.wav"

        self.corrupted_file = self.example_folder / "corrupted.wav"

        self.trimmed_file = self.example_folder / "trimmed.wav"

        self.custom_analysis_results = pd.read_csv(
            self.testpath / Path("custom_results.csv")
        )

        self.default_analysis_results = pd.read_csv(
            self.testpath / Path("default_results.csv")
        )

        self.google_analysis_results = pd.read_csv(
            self.testpath / Path("google_results_minconf025.csv")
        )


@pytest.fixture
def recording_fx():
    return RecordingFixture()
