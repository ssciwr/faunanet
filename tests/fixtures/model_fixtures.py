import sys

sys.path.append("../src/iSparrow")
from src.iSparrow import utils

from pathlib import Path
import yaml
import pytest


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
            self.gogole_cfg = yaml.safe_load(file)

        self.default_module = utils.load_module(
            str(
                self.models_folder
                / Path(self.default_cfg["Analyzer"]["Model"]["model_path"])
                / "model.py"
            )
        )

        self.custom_module = utils.load_module(
            str(
                self.models_folder
                / Path(self.custom_cfg["Analyzer"]["Model"]["model_path"])
                / "model.py"
            )
        )

        self.google_module = utils.load_module(
            str(
                self.models_folder
                / Path(self.gogole_cfg["Analyzer"]["Model"]["model_path"])
                / "model.py"
            )
        )


@pytest.fixture
def model_fx():
    return ModelFixture()
