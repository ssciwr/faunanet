import pytest
from pathlib import Path
import yaml
from iSparrow import utils


def make_preprocessor(cfg_name: str):
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

    with open(testpath / cfg_name, "r") as file:
        cfg = yaml.safe_load(file)

    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    # README: I'm not entirely sure how robust this is...
    module = utils.load_module(
        "pp",
        str(
            models_folder
            / Path(cfg["Analysis"]["Model"]["model_path"])
            / "preprocessor.py"
        ),
    )

    preprocessor = module.Preprocessor.from_cfg(cfg["Data"]["Preprocessor"])

    filepath = example_folder / "soundscape.wav"
    trimmedpath = example_folder / "trimmed.wav"

    return preprocessor, cfg, example_folder, filepath, trimmedpath


@pytest.fixture
def preprocessor_fx():
    return make_preprocessor("cfg_default.yml")


@pytest.fixture
def preprocessor_fx_google():
    return make_preprocessor("cfg_google.yml")
