import pytest
from pathlib import Path
import yaml
from iSparrow import utils
import iSparrow.sparrow_setup as sps


def make_preprocessor(cfg_name: str):
    """
    sets up fixture a preprocessor thatś build with the wrong file paths -> reading must fail
    """

    filepath = Path(__file__).resolve()
    testpath = filepath.parent.parent
    home = Path(sps.SPARROW_HOME)
    models_folder = home / "models"
    example_folder = home / "example"

    with open(testpath / Path("test_configs") / cfg_name, "r") as file:
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
