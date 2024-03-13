import pytest
from pathlib import Path
import importlib
import yaml

# provides setup for preprocessor taht is set up with wrong arguments


@pytest.fixture
def wrong_paths_fx():
    test_path = Path(__file__).resolve().parent.parent

    with open(test_path / Path("example") / "test.yml", "r") as file:
        cfg = yaml.safe_load(file)

    # change the model name to something nonsensical
    cfg["Analyzer"]["Model"]["model_dir"] = "does_not_exist"

    # this is still correct to be able to set up all the classes
    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    pp = importlib.import_module('models.' + cfg["Analyzer"]["Model"]["model_name"] + '.preprocessor')

    preprocessor = pp.Preprocessor(cfg["Data"]["Preprocessor"])

    return preprocessor, cfg, test_path
