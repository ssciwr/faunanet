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
        models_folder = self.sparrow_folder / "models"

        with open(self.testpath / "cfg.yml", "r") as file:
            self.custom_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_default.yml", "r") as file:
            self.default_cfg = yaml.safe_load(file)

        with open(self.testpath / "cfg_wrong_model.yml", "r") as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        with open(self.testpath / "cfg_google.yml", "r") as file:
            self.cfg_google = yaml.safe_load(file)

        self.module = utils.load_module(
            str(
                models_folder
                / Path(cfg["Analyzer"]["Model"]["model_name"])
                / "preprocessor.py"
            )
        )


@pytest.fixture
def model_fx():
    return ModelFixture()
