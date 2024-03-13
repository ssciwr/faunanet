import pytest
from pathlib import Path
import importlib
import yaml


@pytest.fixture
def preprocessor_fx():
    """
    sets up fixture a preprocessor thatś build with the wrong file paths -> reading must fail
    """

    sparrow_folder = Path.home() / Path("iSparrow")

    data_folder = sparrow_folder / Path("data")

    with open(data_folder / "cfg_default.yml", "r") as file:
        cfg = yaml.safe_load(file)

    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    pp = importlib.import_module('models.' + cfg["Analyzer"]["Model"]["model_name"] + '.preprocessor')

    preprocessor = pp.preprocessor_from_config(cfg["Data"]["Preprocessor"])

    filepath = data_folder / "soundscape.wav"
    trimmedpath = data_folder / "trimmed.wav"

    return preprocessor, cfg, data_folder, filepath, trimmedpath
