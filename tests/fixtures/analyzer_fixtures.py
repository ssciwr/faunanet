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

        with open(self.test_path / Path("example") / "cfg.yml", "r") as file:
            self.cfg = yaml.safe_load(file)

        with open(self.test_path / Path("example") / "cfg_missing.yml", "r") as file:
            self.cfg_missing = yaml.safe_load(file)

        with open(self.test_path / Path("example") / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        with open(self.test_path / Path("example") / "cfg_wrong_model.yml", "r") as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        with open(self.test_path / Path("example") / "cfg_species_list.yml", "r") as file:
            self.cfg_species_list = yaml.safe_load(file)

        with open(self.test_path / Path("example") / "cfg_wrong_species_list.yml", "r") as file:
            self.cfg_wrong_species_list = yaml.safe_load(file)


@pytest.fixture
def analyzer_fx():
    return AnalyzerFixture()
