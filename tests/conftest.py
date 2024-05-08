import multiprocessing

multiprocessing.set_start_method("spawn", True)
import pytest
import shutil

from pathlib import Path
import os
import tempfile
from platformdirs import user_cache_dir, user_config_dir
import pooch
import yaml

from iSparrow.utils import read_yaml, load_module

from .fixtures.recording_fixtures import RecordingFixture
from .fixtures.model_fixtures import ModelFixture
from .fixtures.watcher_fixtures import WatchFixture

# set test mode
os.environ["SPARROW_TEST_MODE"] = "True"

# set up the test directories and download the example files


@pytest.fixture()
def make_folders():
    """
    make_folders set up and dipose of a mock sparrow installation in a temporary directory
    """
    tmpdir = tempfile.mkdtemp()

    # create directories
    directories = {
        "home": Path(tmpdir, "iSparrow_tests"),
        "data": Path(tmpdir, "iSparrow_tests_data"),
        "models": Path(tmpdir, "iSparrow_tests", "models"),
        "example": Path(tmpdir, "iSparrow_tests", "example"),
        "output": Path(tmpdir, "iSparrow_tests_output"),
        "cache": Path(user_cache_dir(), "iSparrow_tests"),
        "config": Path(user_config_dir(), "iSparrow_tests"),
    }

    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)

    yield tmpdir, directories  # yield directories instead of nothing

    # remove again after usage
    for name, path in directories.items():
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def load_files(make_folders):
    """
    load_files download all the data files needed for iSparrow to run, but without going via the setup routine.
    """

    tmpdir, directories = make_folders
    ise = directories["example"]
    ism = directories["models"]

    if Path(directories["example"]).exists() is False:
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

    models_data = pooch.create(
        path=pooch.os_cache("iSparrow_downloads"),
        base_url="https://huggingface.co/MaHaWo/iSparrow_test_models/resolve/main",
        registry=(model_file_names | label_file_names | model_code | preprocessor_code),
    )

    for name in [
        "model.tflite",
        "labels.txt",
        "species_presence_model.tflite",
        "model.py",
        "preprocessor.py",
    ]:
        (ism / Path("birdnet_default")).mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(models_data.fetch(f"birdnet_default_v2.4/{name}", progressbar=False)),
            ism / Path("birdnet_default"),
        )

    for name in ["model.tflite", "labels.txt", "model.py", "preprocessor.py"]:
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

    yield tmpdir, directories


# the install fixture provides a basic environment in the system's temporary directory


@pytest.fixture()
def install(load_files):
    """
    install Bundle mock install and data download into a fixture
    """
    tmpdir, directories = load_files

    # make a dummy data directory
    data = Path.home() / "iSparrow_tests_data"
    data.mkdir(parents=True, exist_ok=True)

    yield tmpdir, directories

    # remove the dummy data directory
    shutil.rmtree(data)


# the model fixture is just a thin wrapper around the ModelFixture class
@pytest.fixture
def model_fx(install):
    _, directories = install
    yield ModelFixture(
        directories["home"], directories["output"], directories["models"]
    )


# preprocessors make use of a factory function that then lands in the fixture
@pytest.fixture()
def preprocessor_fx(install):
    """
    sets up fixture a preprocessor thatś build with the wrong file paths -> reading must fail
    """

    _, directories = install

    filepath = Path(__file__).resolve()
    testpath = filepath.parent

    with open(testpath / Path("test_configs") / "cfg_default.yml", "r") as file:
        cfg_default = yaml.safe_load(file)

    with open(testpath / Path("test_configs") / "cfg_google.yml", "r") as file:
        cfg_google = yaml.safe_load(file)

    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    # README: I'm not entirely sure how robust this is...
    module_default = load_module(
        "pp",
        str(
            directories["models"]
            / Path(cfg_default["Analysis"]["Model"]["model_path"])
            / "preprocessor.py"
        ),
    )

    module_google = load_module(
        "ppg",
        str(
            directories["models"]
            / Path(cfg_google["Analysis"]["Model"]["model_path"])
            / "preprocessor.py"
        ),
    )

    filepath = directories["example"] / "soundscape.wav"
    trimmedpath = directories["example"] / "trimmed.wav"

    yield module_default, module_google, cfg_default, cfg_google, directories[
        "example"
    ], filepath, trimmedpath


# recording fixture is a thin wrapper around the RecordingFixture class
@pytest.fixture
def recording_fx(install):
    _, directories = install
    yield RecordingFixture(
        directories["home"], directories["models"], directories["example"]
    )


@pytest.fixture
def watch_fx(install):
    _, directories = install
    yield directories, WatchFixture(
        directories["home"],
        directories["data"],
        directories["output"],
        directories["models"],
    )
