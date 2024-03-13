from pathlib import Path
import yaml
import pytest


class AnalyzerFixture:
    """
    Provide data for setup of analyzers for testing

    """

    def __init__(self):

        self.sparrow_folder = Path.home() / Path("iSparrow")

        self.data_path = self.sparrow_folder / Path("data")

        with open(self.data_path / "cfg.yml", "r") as file:
            self.cfg = yaml.safe_load(file)

        with open(self.data_path / "cfg_missing.yml", "r") as file:
            self.cfg_missing = yaml.safe_load(file)

        with open(self.data_path / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        with open(self.data_path / "cfg_wrong_model.yml", "r") as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        with open(self.data_path / "cfg_species_list.yml", "r") as file:
            self.cfg_species_list = yaml.safe_load(file)

        with open(self.data_path / "cfg_wrong_species_list.yml", "r") as file:
            self.cfg_wrong_species_list = yaml.safe_load(file)


@pytest.fixture
def analyzer_fx():
    return AnalyzerFixture()
