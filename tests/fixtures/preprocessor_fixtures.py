import pytest
from pathlib import Path
import yaml
import importlib
import importlib.util


def load_module(path: str):
    spec = importlib.util.spec_from_file_location("pp", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def preprocessor_fx():
    """
    sets up fixture a preprocessor thatś build with the wrong file paths -> reading must fail
    """

    filepath = Path(__file__).resolve()
    testpath = filepath.parent.parent
    cfgpath = filepath.parent.parent.parent / Path("config") / Path("install_cfg.yml")
    with open(cfgpath, "r") as file:
        sparrow_cfg = yaml.safe_load(file)
        sparrow_cfg = sparrow_cfg["Directories"]

    sparrow_folder = Path(sparrow_cfg["home"]).expanduser()
    models_folder = sparrow_folder / "models"
    example_folder = sparrow_folder / "example"

    with open(testpath / "cfg_default.yml", "r") as file:
        cfg = yaml.safe_load(file)

    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    # README: I'm not entirely sure how robust this is...
    module = load_module(
        str(
            models_folder
            / Path(cfg["Analyzer"]["Model"]["model_name"])
            / "preprocessor.py"
        )
    )

    preprocessor = module.preprocessor_from_config(cfg["Data"]["Preprocessor"])

    filepath = example_folder / "soundscape.wav"
    trimmedpath = example_folder / "trimmed.wav"

    return preprocessor, cfg, example_folder, filepath, trimmedpath
