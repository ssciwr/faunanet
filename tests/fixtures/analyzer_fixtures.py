from pathlib import Path
import yaml
import pytest


class AnalyzerFixture:
    """
    Provide data for setup of analyzers for testing

    """

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

        with open(self.testpath / "cfg.yml", "r") as file:
            self.cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_missing.yml", "r") as file:
            self.cfg_missing = yaml.safe_load(file)

        with open(self.testpath / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_wrong_model.yml", "r") as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        with open(self.testpath / "cfg_species_list.yml", "r") as file:
            self.cfg_species_list = yaml.safe_load(file)

        with open(self.testpath / "cfg_wrong_species_list.yml", "r") as file:
            self.cfg_wrong_species_list = yaml.safe_load(file)


@pytest.fixture
def analyzer_fx():
    return AnalyzerFixture()
