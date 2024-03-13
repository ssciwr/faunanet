import pytest
from pathlib import Path
import importlib
import yaml


@pytest.fixture
def preprocessor_fx():
    """
    sets up fixture a preprocessor thatś build with the wrong file paths -> reading must fail
    """
    test_path = Path(__file__).resolve().parent.parent

    with open(test_path / Path("example") / "cfg_default.yml", "r") as file:
        cfg = yaml.safe_load(file)

    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    pp = importlib.import_module('models.' + cfg["Analyzer"]["Model"]["model_name"] + '.preprocessor')

    preprocessor = pp.preprocessor_from_config(cfg["Data"]["Preprocessor"])

    filepath = test_path / "example/soundscape.wav"
    trimmedpath = test_path / "example/trimmed.wav"

    return preprocessor, cfg, test_path, filepath, trimmedpath
