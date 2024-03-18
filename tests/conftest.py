import pytest
import shutil
import pooch
import yaml
from pathlib import Path

from .fixtures.recording_fixtures import recording_fx
from .fixtures.preprocessor_fixtures import preprocessor_fx, preprocessor_fx_google
from .fixtures.analyzer_fixtures import analyzer_fx
from .fixtures.model_fixtures import model_fx


# README: the below will later land in setup.py...
def read_yaml(path: str):
    print(f"...reading config from {path}")
    """
        read_yaml Read the yaml basic config file for iSparrow from path.
                It contains the install directory, data directory and other things used
                by iSparrow internally.

        Args:
            path (str): Path to the yaml base config.

        Returns:
            dict: read base config file.
        """

    if Path(path).exists() is False:
        raise FileNotFoundError(f"The folder {path} does not exist")

    with open(Path(path)) as file:
        base_cfg = yaml.safe_load(file)

    return base_cfg


def make_directories(base_cfg_dirs: dict):
    """
    make_directories _summary_


    Args:
        base_cfg_dirs (dict): _description_

    Raises:
        KeyError: A folder given in the config does not exist

    Returns:
        tuple: created folders: (isparrow-homefolder, modelsfolder, datafolder, outputfolder, examplefolder)
    """
    print("...Making direcotries...")
    if "home" not in base_cfg_dirs:
        raise KeyError("The home folder for iSparrow must be given in the base config")

    if "models" not in base_cfg_dirs:
        raise KeyError(
            "The models folder for iSparrow must be given in the base config"
        )

    if "data" not in base_cfg_dirs:
        raise KeyError("The data folder for iSparrow must be given in the base config")

    if "output" not in base_cfg_dirs:
        raise KeyError(
            "The output folder for iSparrow must be given in the base config"
        )

    ish = Path(base_cfg_dirs["home"]).expanduser().resolve()
    ism = Path(base_cfg_dirs["models"]).expanduser().resolve()
    isd = Path(base_cfg_dirs["data"]).expanduser().resolve()
    iso = Path(base_cfg_dirs["output"]).expanduser().resolve()
    ise = (Path(base_cfg_dirs["home"]).expanduser() / Path("example")).resolve()

    print(ish, ism, isd, iso, ise)
    for p in [ish, ism, isd, iso, ise]:
        p.mkdir(parents=True, exist_ok=True)

    return ish, ism, isd, iso, ise


def download_model_files(isparrow_model_dir: str):
    """
    download_model_files Download models and class labels that iSparrow needs to analyze and classify audio data.

    Args:
        isparrow_homedir (str): Path to the main iSparrow directory
    """

    print("... Downloading model files...")

    ism = Path(isparrow_model_dir)

    if ism.exists() is False:
        raise FileNotFoundError(f"The folder {isparrow_model_dir} does not exist")

    # have filenames and checksum hardcoded for now. "None" indicates unknown or changing filenames
    model_file_names = {
        "birdnet_default_v2.4/model.tflite": "sha256:55f3e4055b1a13bfa9a2452731d0d34f6a02d6b775a334362665892794165e4c",
        "birdnet_custom_v2.4/model.tflite": "sha256:5eee37652430c54490321e0d2096d55817b4ac4da2301b594f03fcb9d52af741",
        "google_bird_classification/saved_model.pb": "sha256:c6bdf0c2659f6d4713c670b92cceb083f8c1b401aee79ef6912614a1d89b6f97",
        "google_bird_classification/variables/variables.index": None,
        "google_bird_classification/variables/variables.data-00000-of-00001": "sha256:d967ea7bfaccdcfe4ff59f8d9f3bdec69181e4e79fd7abebf692100efcdfcc56",
    }

    label_file_names = {
        "birdnet_default_v2.4/labels.txt": None,
        "birdnet_custom_v2.4/labels.txt": None,
        "google_bird_classification/assets/family.csv": None,
        "google_bird_classification/assets/genus.csv": None,
        "google_bird_classification/assets/label.csv": None,
        "google_bird_classification/assets/order.csv": None,
        "google_bird_classification/labels.txt": None,
        "google_bird_classification/train_metadata.csv": None,
    }

    models_data = pooch.create(
        path=pooch.os_cache("iSparrow"),
        base_url="https://huggingface.co/MaHaWo/iSparrow_test_models/resolve/main",
        registry=(model_file_names | label_file_names),
    )

    for name in ["model.tflite", "labels.txt"]:
        (ism / Path("birdnet_default")).mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(models_data.fetch(f"birdnet_default_v2.4/{name}", progressbar=False)),
            ism / Path("birdnet_default"),
        )

    for name in ["model.tflite", "labels.txt"]:
        (ism / Path("birdnet_custom")).mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Path(models_data.fetch(f"birdnet_custom_v2.4/{name}", progressbar=False)),
            ism / Path("birdnet_custom"),
        )

    for name in ["saved_model.pb", "labels.txt", "train_metadata.csv"]:
        (ism / Path("google_perch")).mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Path(
                models_data.fetch(
                    f"google_bird_classification/{name}", progressbar=False
                )
            ),
            ism / Path("google_perch"),
        )

    # assets and variables need to live in separate directories to load the model correctly
    for name in [
        "variables/variables.index",
        "variables/variables.data-00000-of-00001",
    ]:

        (ism / Path("google_perch") / "variables").mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Path(
                models_data.fetch(
                    f"google_bird_classification/{name}", progressbar=False
                )
            ),
            ism / Path("google_perch") / "variables",
        )

    for name in [
        "assets/family.csv",
        "assets/genus.csv",
        "assets/label.csv",
        "assets/order.csv",
    ]:

        (ism / Path("google_perch") / "assets").mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Path(
                models_data.fetch(
                    f"google_bird_classification/{name}", progressbar=False
                )
            ),
            ism / Path("google_perch") / "assets",
        )


def download_example_data(isparrow_example_dir: str):
    """
    download_example_data Download the example audio files used by iSparrow for its tests and examples.

    Args:
        isparrow_example_dir (str): Path to the iSparrow example directory
    """

    print("... Downloading example files...")

    ise = Path(isparrow_example_dir)

    if ise.exists() is False:
        raise FileNotFoundError(f"The folder {isparrow_example_dir} does not exist")

    # create registries to pull files from. haddcode names and hashes for now
    example_data_file_names = {
        "corrupted.wav": "sha256:68cbc7c63bed90c2ad4fb7d3b5cc608c82cebeaf5e91d5e8d6793d8645b30b95",
        "soundscape.wav": "sha256:df312b45bc82ce4c638c3e9e09d748702ea14a91ec29e4e8e0676d3e3e015fd7",
        "trimmed.wav": "sha256:a4b3c078d2c617264dc5e6a0d62deedba9232699580c9c73d237496726c194b3",
        "species_list.txt": None,
    }

    example_data = pooch.create(
        path=pooch.os_cache("iSparrow"),
        base_url="https://huggingface.co/datasets/MaHaWo/iSparrow_test_data/resolve/main",
        registry=example_data_file_names,
    )

    # don't leave them in the cached folder but copy to where user can actually see them.
    for name in example_data_file_names.keys():
        shutil.copy(
            Path(example_data.fetch(name, progressbar=False)),
            ise,
        )


def copy_files(modeldir):
    """
    copy the current preprocessors into the model directory, as is intended later
    """
    current = Path(__file__).resolve().parent
    local_pp_dir = current.parent / "models"

    for name in ["birdnet_default", "birdnet_custom", "google_perch"]:
        shutil.copy(
            local_pp_dir / Path(name) / "preprocessor.py", Path(modeldir) / Path(name)
        )
        shutil.copy(local_pp_dir / Path(name) / "model.py", Path(modeldir) / Path(name))
        shutil.copy(
            local_pp_dir / Path(name) / "__init__.py", Path(modeldir) / Path(name)
        )


# add a fixture with session scope that emulates the result of a later to-be-implemented-install-routine
@pytest.fixture(scope="session", autouse=True)
def install(request):
    print("Creating iSparrow folders and downloading data... ")
    # user cfg can override stuff that the base cfg has. When the two are merged, the result has
    # the base_cfg values whereever user does not have anything

    cfg_path = Path(__file__).resolve().parent.parent / "config"

    cfg = read_yaml(cfg_path / Path("install_cfg.yml"))

    home, models, data, output, examples = make_directories(cfg["Directories"])

    download_model_files(models.resolve())

    download_example_data(examples.resolve())

    copy_files(models.resolve())

    shutil.copy(cfg_path / Path("install_cfg.yml"), home)

    print("Installation finished")

    # remove again after usage
    def teardown():
        shutil.rmtree(str(home))
        shutil.rmtree(str(data))
        shutil.rmtree(str(output))

    request.addfinalizer(teardown)
