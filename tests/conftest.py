import multiprocessing
import pytest
import shutil

from pathlib import Path
import os
import tempfile
from platformdirs import user_cache_dir, user_config_dir
import yaml

from faunanet.utils import load_module
from faunanet.faunanet_setup import download_example_data, download_model_files
from .fixtures.recording_fixtures import RecordingFixture
from .fixtures.model_fixtures import ModelFixture
from .fixtures.watcher_fixtures import WatchFixture

multiprocessing.set_start_method("spawn", True)

# set test mode
os.environ["FAUNANET_TEST_MODE"] = "True"


def read_yaml_with_replacement(path, dir):

    with open(Path(path)) as file:
        cfg = yaml.safe_load(file)

    def update_recursive(d):
        for k, v in d.items():
            if isinstance(v, dict):
                update_recursive(v)
            else:
                if isinstance(v, str):
                    d[k] = v.replace("~", str(dir))

    update_recursive(cfg)

    if "Data" in cfg.keys():
        cfg["Data"]["input"] = str(Path(dir, "faunanet_tests_data"))
        cfg["Data"]["output"] = str(Path(dir, "faunanet_tests_output"))

    return cfg


@pytest.fixture()
def patch_functions(mocker, tmpdir):
    mocker.patch("faunanet.repl.user_cache_dir", new=lambda: Path(tmpdir) / "cache")
    mocker.patch("faunanet.repl.user_config_dir", new=lambda: Path(tmpdir) / "config")
    mocker.patch(
        "faunanet.repl.read_yaml", new=lambda f: read_yaml_with_replacement(f, tmpdir)
    )
    mocker.patch(
        "faunanet.faunanet_setup.user_cache_dir", new=lambda: Path(tmpdir) / "cache"
    )
    mocker.patch(
        "faunanet.faunanet_setup.user_config_dir", new=lambda: Path(tmpdir) / "config"
    )
    mocker.patch(
        "faunanet.faunanet_setup.utils.read_yaml",
        new=lambda f: read_yaml_with_replacement(f, tmpdir),
    )
    yield tmpdir


# set up the test directories and download the example files
@pytest.fixture(scope="session")
def make_faunanet_home():
    """
    make_faunanet_home Make simulated faunanet setup in a temporary directory


    Yields:
        dictionary: dictionary with the paths to the created directories
    """
    tmpdir = tempfile.mkdtemp()

    # create directories
    directories = {
        "home": Path(tmpdir, "faunanet_tests"),
        "models": Path(tmpdir, "faunanet_tests", "models"),
        "example": Path(tmpdir, "faunanet_tests", "example"),
        "cache": Path(user_cache_dir(), "faunanet_tests"),
        "config": Path(user_config_dir(), "faunanet_tests"),
    }

    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)

    yield tmpdir, directories  # yield directories instead of nothing

    # remove again after usage
    shutil.rmtree(tmpdir)


@pytest.fixture()
def make_folders(make_faunanet_home):
    """
    make_folders set up and dipose of a mock faunanet installation in a temporary directory
    """
    tmpdir, directories = make_faunanet_home

    # create directories

    directories["data"] = Path(tmpdir, "faunanet_tests_data")
    directories["output"] = Path(tmpdir, "faunanet_tests_output")

    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)

    yield tmpdir, directories  # yield directories instead of nothing

    # remove again after usage
    for name in ["data", "output"]:
        shutil.rmtree(directories[name], ignore_errors=True)


@pytest.fixture(scope="session")
def load_files(make_faunanet_home):
    """
    load_files download all the data files needed for faunanet to run, but without going via the setup routine.
    """

    tmpdir, directories = make_faunanet_home
    ise = directories["example"]
    ism = directories["models"]

    download_example_data(ise)
    download_model_files(ism)

    yield tmpdir, directories

    # no cleanup here because rmtree will do that in 'make_folders'


# the install fixture provides a basic environment in the system's temporary directory
@pytest.fixture()
def install(load_files, make_folders):
    """
    install Bundle mock install and data download into a fixture
    """
    tmpdir, directories = load_files

    # make a dummy data directory
    data = Path.home() / "faunanet_tests_data"
    data.mkdir(parents=True, exist_ok=True)

    yield tmpdir, directories

    # remove the dummy data directory
    shutil.rmtree(data)


@pytest.fixture()
def clean_up_test_installation():
    yield  # This is where the test runs

    # clean up stuff
    for path in [
        Path("~/faunanet_tests").expanduser(),
        Path("~/faunanet_tests_data").expanduser(),
        Path("~/faunanet_tests/models").expanduser(),
        Path("~/faunanet_tests/example").expanduser(),
        Path("~/faunanet_tests_output").expanduser(),
        Path(user_cache_dir()) / "faunanet_tests",
        Path(user_config_dir()) / "faunanet_tests",
    ]:
        print("deleting folder @", path)
        if path.exists():
            shutil.rmtree(path)


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
