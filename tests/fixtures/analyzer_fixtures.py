from pathlib import Path
import yaml
from copy import deepcopy
import pytest


class AnalyzerFixture:
    """
    Provide data for setup of analyzers for testing

    """

    def __init__(self):

        self.test_path = Path(__file__).resolve().parent.parent

        with open(self.test_path / Path("example") / "test.yml", "r") as file:
            self.cfg = yaml.safe_load(file)

        self.default_cfg = deepcopy(self.cfg)
        
        self.default_cfg["Analyzer"]["Model"]["model_name"] = "birdnet_defaults"

        self.cfg_missing = deepcopy(self.cfg)

        del self.cfg_missing["Analyzer"]["Model"][
            "model_name"
        ]  # model_name missing -> should load default
        del self.cfg_missing["Analyzer"]["Model"]["apply_sigmoid"]
        del self.cfg_missing["Analyzer"]["Model"]["sigmoid_sensitivity"]
        del self.cfg_missing["Analyzer"]["Model"]["num_threads"]

        self.cfg_wrong = deepcopy(self.cfg)

        self.cfg_wrong["Analyzer"]["Model"]["model_name"] = "wrong_model_name"

        self.wrong_custom_species_list_path = "some_really_wrong_path"

        self.wrong_custom_species_list_path = "some_other_really_wrong_path"


@pytest.fixture
def analyzer_fx():
    return AnalyzerFixture()
