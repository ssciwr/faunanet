import pytest
from pathlib import Path
import yaml
import sys
import pandas as pd

sys.path.append("../src/iSparrow")

from src.iSparrow import sparrow_analyzer as spa
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
            self.cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        # import preprocessor definition that we need

        pp = utils.load_module(
            "pp",
            str(
                self.models_folder
                / Path(self.cfg["Analyzer"]["Model"]["model_path"])
                / "preprocessor.py"
            )
        )

        ppd = utils.load_module(
            "ppd",
            str(
                self.models_folder
                / Path(self.cfg["Analyzer"]["Model"]["model_path"])
                / "preprocessor.py"
            )
        )

        self.preprocessor = pp.Preprocessor.from_cfg(self.cfg["Data"]["Preprocessor"])

        self.analyzer = spa.SparrowAnalyzer.from_cfg(
            str(self.sparrow_folder), self.cfg["Analyzer"]
        )

        self.default_analyzer = spa.SparrowAnalyzer.from_cfg(
            str(self.sparrow_folder), self.default_cfg["Analyzer"]
        )

        self.default_preprocessor = ppd.Preprocessor.from_cfg(
            self.default_cfg["Data"]["Preprocessor"]
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


@pytest.fixture
def recording_fx():

    return RecordingFixture()
