import shutil
import pooch
import yaml
import os
from pathlib import Path
from platformdirs import user_config_dir, user_cache_dir
from iSparrow import utils
from importlib.resources import files
import iSparrow

SPARROW_HOME = None
SPARROW_MODELS = None
SPARROW_OUTPUT = None
SPARROW_EXAMPLES = None
SPARROW_CONFIG = None
SPARROW_CACHE = None


def make_directories(base_cfg_dirs: dict):
    """
    make_directories Make all the directories for sparrow.


    Args:
        base_cfg_dirs (dict): Dictionary containing paths for the main install ("home"),
        the directory where models are stored ("models"),
        and the "output" directory to store inference results and potentially other data in ("output")
    Raises:
        KeyError: A folder given in the config does not exist

    Returns:
        tuple: created folders: (isparrow-homefolder, modelsfolder, datafolder, outputfolder, examplefolder)
    """
    if "home" not in base_cfg_dirs:
        raise KeyError("The home folder for iSparrow must be given in the base config")

    if "models" not in base_cfg_dirs:
        raise KeyError(
            "The models folder for iSparrow must be given in the base config"
        )

    if "output" not in base_cfg_dirs:
        raise KeyError(
            "The output folder for iSparrow must be given in the base config"
        )

    ish = Path(base_cfg_dirs["home"]).expanduser().resolve()
    ism = Path(base_cfg_dirs["models"]).expanduser().resolve()
    iso = Path(base_cfg_dirs["output"]).expanduser().resolve()
    ise = (Path(base_cfg_dirs["home"]).expanduser() / Path("example")).resolve()
    iscfg = Path(user_config_dir()) / "iSparrow"
    iscache = Path(user_cache_dir()) / "iSparrow"

    if os.getenv("SPARROW_TEST_MODE") == "True":
        iscfg = Path(user_config_dir()) / "iSparrow_tests"
        iscache = Path(user_cache_dir()) / "iSparrow_tests"

    for p in [ish, ism, iso, ise]:
        p.mkdir(parents=True, exist_ok=False)

    for p in [iscfg, iscache]:
        p.mkdir(parents=True, exist_ok=True)

    return ish, ism, iso, ise, iscfg, iscache


def download_model_files(model_dir: str = "models"):
    """
    download_model_files Download default model files for iSparrow. This is required to run before anything else is done with iSparrow.

    Args:
        model_dir (str, optional): Path to put the model files at. Defaults to "models".

    Raises:
        FileNotFoundError: When the model directory does not exist.
    """
    print("... Downloading model files...")

    ism = Path(model_dir)

    if ism.exists() is False:
        raise FileNotFoundError(f"The folder {model_dir} does not exist")

    # have filenames and checksum hardcoded for now. "None" indicates unknown or changing filenames
    model_file_names = {
        "birdnet_default_v2.4/model.tflite": "sha256:55f3e4055b1a13bfa9a2452731d0d34f6a02d6b775a334362665892794165e4c",
        "birdnet_custom_v2.4/model.tflite": "sha256:5eee37652430c54490321e0d2096d55817b4ac4da2301b594f03fcb9d52af741",
        "birdnet_default_v2.4/species_presence_model.tflite": "sha256:1226f23fc20362617deb09178f366111b70cf085c2c82893f2814e5acedce6c2",
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

    model_code = {
        "birdnet_default_v2.4/model.py": None,
        "birdnet_custom_v2.4/model.py": None,
        "google_bird_classification/model.py": None,
    }

    preprocessor_code = {
        "birdnet_default_v2.4/preprocessor.py": None,
        "birdnet_custom_v2.4/preprocessor.py": None,
        "google_bird_classification/preprocessor.py": None,
    }

    config_files = {
        "birdnet_default_v2.4/default.yml": None,
        "birdnet_custom_v2.4/default.yml": None,
        "google_bird_classification/default.yml": None,
    }

    models_data = pooch.create(
        path=pooch.os_cache("iSparrow_downloads"),
        base_url="https://huggingface.co/MaHaWo/iSparrow_test_models/resolve/main",
        registry=(
            model_file_names
            | label_file_names
            | model_code
            | preprocessor_code
            | config_files
        ),
    )

    for name in [
        "model.tflite",
        "labels.txt",
        "species_presence_model.tflite",
        "model.py",
        "preprocessor.py",
        "default.yml",
    ]:
        (ism / Path("birdnet_default")).mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(models_data.fetch(f"birdnet_default_v2.4/{name}", progressbar=False)),
            ism / Path("birdnet_default"),
        )

    for name in [
        "model.tflite",
        "labels.txt",
        "model.py",
        "preprocessor.py",
        "default.yml",
    ]:
        (ism / Path("birdnet_custom")).mkdir(parents=True, exist_ok=True)

        shutil.copy(
            Path(models_data.fetch(f"birdnet_custom_v2.4/{name}", progressbar=False)),
            ism / Path("birdnet_custom"),
        )

    for name in [
        "saved_model.pb",
        "labels.txt",
        "train_metadata.csv",
        "model.py",
        "preprocessor.py",
        "default.yml",
    ]:
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


def download_example_data(example_dir: str = "examples"):
    """
    download_example_data Download the example audio files used by iSparrow for its tests and examples.

    Args:
        example_dir (str, optional): Path to the iSparrow example directory. Defaults to 'examples'.
    """

    print("... Downloading example files...")

    ise = Path(example_dir)

    if ise.exists() is False:
        raise FileNotFoundError(f"The folder {example_dir} does not exist")

    # create registries to pull files from. hardcode names and hashes for now
    example_data_file_names = {
        "corrupted.wav": "sha256:68cbc7c63bed90c2ad4fb7d3b5cc608c82cebeaf5e91d5e8d6793d8645b30b95",
        "soundscape.wav": "sha256:df312b45bc82ce4c638c3e9e09d748702ea14a91ec29e4e8e0676d3e3e015fd7",
        "trimmed.wav": "sha256:a4b3c078d2c617264dc5e6a0d62deedba9232699580c9c73d237496726c194b3",
        "species_list.txt": None,
    }

    example_data = pooch.create(
        path=pooch.os_cache("iSparrow_downloads"),
        base_url="https://huggingface.co/datasets/MaHaWo/iSparrow_test_data/resolve/main",
        registry=example_data_file_names,
    )

    # don't leave them in the cached folder but copy to where user can actually see them.
    for name in example_data_file_names.keys():
        shutil.copy(
            Path(example_data.fetch(name, progressbar=False)),
            ise,
        )


def set_up_sparrow(custom_config: str = None):
    """
    set_up_sparrow Set up the iSparrow directories and download the necessary data. This is required to run before anything else is done with iSparrow.

    Args:
        custom_config (str, optional): Path to a custom installation file. See the 'install.yml' file provided with this package for possible customization options. Defaults to None.

    Raises:
        FileExistsError: When there is an existing iSparrow installation.
    """
    print("Creating iSparrow folders and downloading data... ")

    packagebase = files(iSparrow)
    install_cfg = utils.read_yaml(packagebase / "install.yml")

    if custom_config is not None:
        custom_install_config = utils.read_yaml(custom_config)
        utils.update_dict_leafs_recursive(install_cfg, custom_install_config)

    for key in ["home", "models", "output"]:
        if Path(install_cfg["Directories"][key]).expanduser().resolve().exists():
            raise FileExistsError(
                f"{key} directory already exists. Please remove it before running the installation."
            )

    home, models, output, examples, config, cache = make_directories(
        install_cfg["Directories"]
    )

    if Path(config, "install.yml").exists():

        with open(Path(config) / "install.yml", "r") as yfile:
            old_cfg = yaml.safe_load(yfile)["Directories"]
            old_dirs = [Path(p).expanduser().resolve() for p in old_cfg.values()]

        for dir in [home, models, output, examples, config, cache]:

            # avoid compromising existing installations
            if Path(dir).exists() and Path(dir).expanduser().resolve() not in old_dirs:
                shutil.rmtree(dir)
        p = Path(config, "install.yml")
        raise FileExistsError(
            f"An iSparrow installation already exists at {p}. Please remove it before running the installation."
        )

    with open(Path(config) / "install.yml", "w") as yfile:
        yaml.safe_dump(install_cfg, yfile)
    shutil.copy(packagebase / "default.yml", config)

    download_model_files(model_dir=models.resolve())

    download_example_data(example_dir=examples.resolve())

    global SPARROW_HOME, SPARROW_MODELS, SPARROW_OUTPUT, SPARROW_EXAMPLES, SPARROW_CACHE, SPARROW_CONFIG

    SPARROW_HOME = home
    SPARROW_MODELS = models
    SPARROW_OUTPUT = output
    SPARROW_EXAMPLES = examples
    SPARROW_CACHE = cache
    SPARROW_CONFIG = config

    print("Installation finished")