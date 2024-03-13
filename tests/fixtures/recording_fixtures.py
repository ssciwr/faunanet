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
        self.test_path = Path(__file__).resolve().parent.parent

        print("test path: ", self.test_path)

        with open(self.test_path / Path("example") / "test.yml", "r") as file:
            self.cfg = yaml.safe_load(file)
        # import preprocessor definition that we need
        pp = importlib.import_module(
            "models." + self.cfg["Analyzer"]["Model"]["model_name"] + ".preprocessor"
        )

        self.preprocessor = pp.Preprocessor(self.cfg["Data"]["Preprocessor"])

        self.analyzer = spa.SparrowAnalyzer(self.cfg["Analyzer"])

        self.good_file = self.test_path / "example/soundscape.wav"

        self.corrupted_file = self.test_path / "example/corrupted.wav"

        self.trimmed_file = self.test_path / "example/trimmed.wav"

        self.custom_analysis_results = pd.read_csv(
            self.test_path / Path("example") / Path("custom_results.csv")
        )

        self.default_analysis_results = pd.read_csv(
            self.test_path / Path("example") / Path("default_results.csv")
        )




@pytest.fixture
def recording_fx():

    return RecordingFixture()
