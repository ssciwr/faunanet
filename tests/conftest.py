import multiprocessing
import pytest
import shutil
import pathlib
import tempfile
import platformdirs
import yaml
from importlib.resources import files

import iSparrow
from .fixtures.recording_fixtures import RecordingFixture
from .fixtures.model_fixtures import ModelFixture
from .fixtures.watcher_fixtures import WatchFixture

multiprocessing.set_start_method("spawn", True)


def path_redirects(tmp_path, mockerfunc):
    # putting this into an extra function enables overriding fixtures using this 
    # in individual modules, which is needed for setup tests
    mockerfunc.patch(
        "platformdirs.user_cache_dir",
        return_value=pathlib.Path(tmp_path, "cache"),
    )
    mockerfunc.patch(
        "platformdirs.user_config_dir",
        return_value=pathlib.Path(tmp_path, "config"),
    )
    mockerfunc.patch(
        "iSparrow.sparrow_setup.user_config_dir",
        return_value=pathlib.Path(tmp_path, "config"),
    )
    mockerfunc.patch(
        "iSparrow.sparrow_setup.user_cache_dir",
        return_value=pathlib.Path(tmp_path, "cache"),
    )
    mockerfunc.patch(
        "iSparrow.repl.user_config_dir",
        return_value=pathlib.Path(tmp_path, "config"),
    )

    mockerfunc.patch.object(pathlib.Path, "home", new=lambda: tmp_path)

    return tmp_path

@pytest.fixture(scope="session", autouse=True)
def redirect_folders(session_mocker):
    tmp_path = tempfile.mkdtemp()
    yield path_redirects(tmp_path, session_mocker)


# set up the test directories and download the example files
@pytest.fixture(scope="session")
def make_sparrow_home(redirect_folders):
    """
    make_sparrow_home Make simulated sparrow setup in a temporary directory


    Yields:
        dictionary: dictionary with the paths to the created directories
    """
    tmpdir = redirect_folders

    # create directories
    packagebase = files(iSparrow)
    directories = iSparrow.utils.read_yaml(pathlib.Path(packagebase) / "install.yml")[
        "Directories"
    ]

    for name in directories.keys():
        directories[name] = pathlib.Path(directories[name]).expanduser()

    directories["cache"] = pathlib.Path(platformdirs.user_cache_dir(), "iSparrow")
    directories["config"] = pathlib.Path(platformdirs.user_config_dir(), "iSparrow")
    directories["data"] = pathlib.Path(tmpdir, "iSparrow_data").expanduser()

    for name, path in directories.items():
        print(".... make directory: ", name, pathlib.Path(path).expanduser())
        pathlib.Path(path).expanduser().mkdir(parents=True, exist_ok=True)

    yield tmpdir, directories  # yield directories instead of nothing

    # remove again after usage
    for _, path in directories.items():
        if pathlib.Path(path).expanduser().exists():
            shutil.rmtree(path)

    shutil.rmtree(tmpdir)


@pytest.fixture(scope="session")
def load_files(make_sparrow_home):
    """
    load_files download all the data files needed for iSparrow to run, but without going via the setup routine.
    """

    tmpdir, directories = make_sparrow_home
    ise = pathlib.Path(directories["example"]).expanduser()
    ism = pathlib.Path(directories["models"]).expanduser()

    iSparrow.sparrow_setup.download_example_data(ise)
    iSparrow.sparrow_setup.download_model_files(ism)

    yield tmpdir, directories


@pytest.fixture()
def clean_up_test_installation(redirect_folders):
    yield  # This is where the test runs

    cfg = iSparrow.utils.read_yaml(
        pathlib.Path(__file__).parent / "test_install_config" / "install.yml"
    )

    for _, path in cfg["Directories"].items():
        if pathlib.Path(path).expanduser().exists():
            shutil.rmtree(pathlib.Path(path).expanduser())

    for path in [
        pathlib.Path("~/iSparrow_data").expanduser(),
        pathlib.Path("~/iSparrow_output").expanduser(),
        pathlib.Path(platformdirs.user_cache_dir()) / "iSparrow",
        pathlib.Path(platformdirs.user_config_dir()) / "iSparrow",
    ]:

        if path.exists():
            shutil.rmtree(path)


# the install fixture provides a basic environment in the system's temporary directory
@pytest.fixture()
def install(
    load_files,
):
    """
    install Bundle mock install and data download into a fixture
    """
    tmpdir, directories = load_files

    packagebase = files(iSparrow)

    shutil.copy(
        pathlib.Path(packagebase).expanduser() / "install.yml", directories["config"]
    )
    shutil.copy(
        pathlib.Path(packagebase).expanduser() / "default.yml", directories["config"]
    )

    yield tmpdir, directories

    # delete things in data folder again
    for file in pathlib.Path(directories["data"]).expanduser().iterdir():
        if file.is_file():
            file.unlink()

    # delete directories in output folder again
    for folder in pathlib.Path(directories["output"]).iterdir():
        shutil.rmtree(folder.expanduser())


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

    filepath = pathlib.Path(__file__)
    testpath = filepath.parent

    with open(testpath / pathlib.Path("test_configs") / "cfg_default.yml", "r") as file:
        cfg_default = yaml.safe_load(file)

    with open(testpath / pathlib.Path("test_configs") / "cfg_google.yml", "r") as file:
        cfg_google = yaml.safe_load(file)

    # README: in later versions when a 'exchange_model'function is present somewhere, this
    # needs respective catches for wrong paths/nonexistant files etc
    # README: I'm not entirely sure how robust this is...
    module_default = iSparrow.utils.load_module(
        "pp",
        str(
            directories["models"]
            / pathlib.Path(cfg_default["Analysis"]["Model"]["model_path"])
            / "preprocessor.py"
        ),
    )

    module_google = iSparrow.utils.load_module(
        "ppg",
        str(
            directories["models"]
            / pathlib.Path(cfg_google["Analysis"]["Model"]["model_path"])
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
