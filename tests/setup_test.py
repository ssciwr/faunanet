import iSparrow
import pathlib
import pytest
import shutil
from .conftest import path_redirects

tflite_file = "model.tflite"


@pytest.fixture(autouse=True)
def redirect_folders(tmp_path, mocker):
    yield path_redirects(tmp_path, mocker)


@pytest.fixture()
def cleanup_after_test(redirect_folders):
    yield  # This is where the test runs

    temp_dir = redirect_folders
    # Cleanup code goes here
    for path in [
        "test_home",
        "test_models",
        "test_output",
        "test_examples",
        "test_cache",
        "test_config",
    ]:
        if pathlib.Path(temp_dir, path).exists():
            shutil.rmtree(pathlib.Path(temp_dir, path))


@pytest.fixture()
def make_folders(redirect_folders):
    temp_dir = redirect_folders
    for path in [
        "test_models",
        "test_examples",
        "test_cache",
    ]:
        pathlib.Path(temp_dir, path).mkdir(parents=True, exist_ok=True)

    yield


def test_make_directories(tmp_path, cleanup_after_test):
    base_cfg_dirs = {
        "home": str(pathlib.Path(tmp_path, "test_home")),
        "models": str(pathlib.Path(tmp_path, "test_models")),
        "output": str(pathlib.Path(tmp_path, "test_output")),
    }
    ish, ism, iso, ise, iscfg, iscache = iSparrow.sparrow_setup.make_directories(
        base_cfg_dirs
    )

    assert ish.exists()
    assert ism.exists()
    assert iso.exists()
    assert ise.exists()
    assert iscfg.exists()
    assert iscache.exists()


def test_make_directories_exceptions(cleanup_after_test):
    base_cfg_dirs = {"models": "test_models", "output": "test_output"}

    with pytest.raises(
        KeyError, match="The home folder for iSparrow must be given in the base config"
    ):
        iSparrow.sparrow_setup.make_directories(base_cfg_dirs)

    base_cfg_dirs = {"home": "test_home", "output": "test_output"}

    with pytest.raises(
        KeyError,
        match="The models folder for iSparrow must be given in the base config",
    ):
        iSparrow.sparrow_setup.make_directories(base_cfg_dirs)

    base_cfg_dirs = {
        "home": "test_home",
        "models": "test_models",
    }

    with pytest.raises(
        KeyError,
        match="The output folder for iSparrow must be given in the base config",
    ):
        iSparrow.sparrow_setup.make_directories(base_cfg_dirs)


def test_download_example_data(tmp_path, make_folders, cleanup_after_test):
    example_dir = str(pathlib.Path(tmp_path, "test_examples"))

    iSparrow.sparrow_setup.download_example_data(example_dir)

    assert pathlib.Path(example_dir).exists()
    assert pathlib.Path(example_dir, "soundscape.wav").is_file()
    assert pathlib.Path(example_dir, "corrupted.wav").is_file()
    assert pathlib.Path(example_dir, "trimmed.wav").is_file()
    assert pathlib.Path(example_dir, "species_list.txt").is_file()


def test_download_example_data_exceptions(make_folders, cleanup_after_test):
    example_dir = "test_examples_nonexistent"
    with pytest.raises(
        FileNotFoundError, match="The folder test_examples_nonexistent does not exist"
    ):
        iSparrow.sparrow_setup.download_example_data(example_dir)


def test_download_model_files(tmp_path, make_folders):
    model_dir = str(pathlib.Path(tmp_path, "test_models"))
    iSparrow.sparrow_setup.download_model_files(model_dir)
    assert pathlib.Path(model_dir).exists()
    assert pathlib.Path(model_dir, "birdnet_default", tflite_file).is_file()
    assert pathlib.Path(model_dir, "birdnet_custom", tflite_file).is_file()
    assert pathlib.Path(model_dir, "google_perch", "saved_model.pb").is_file()


def test_download_model_files_exceptions(make_folders, cleanup_after_test):
    model_dir = "test_models_nonexistent"
    with pytest.raises(
        FileNotFoundError, match="The folder test_models_nonexistent does not exist"
    ):
        iSparrow.sparrow_setup.download_model_files(model_dir)


def test_setup(clean_up_test_installation):
    filepath = pathlib.Path(__file__).parent / "test_install_config" / "install.yml"

    iSparrow.sparrow_setup.set_up_sparrow(filepath)

    assert iSparrow.sparrow_setup.SPARROW_HOME.exists()
    assert iSparrow.sparrow_setup.SPARROW_EXAMPLES.exists()
    assert iSparrow.sparrow_setup.SPARROW_MODELS.exists()
    assert iSparrow.sparrow_setup.SPARROW_OUTPUT.exists()
    assert iSparrow.sparrow_setup.SPARROW_CONFIG.exists()
    assert iSparrow.sparrow_setup.SPARROW_CACHE.exists()

    assert (
        iSparrow.sparrow_setup.SPARROW_MODELS / "birdnet_default" / tflite_file
    ).is_file()
    assert (
        iSparrow.sparrow_setup.SPARROW_MODELS / "birdnet_custom" / tflite_file
    ).is_file()
    assert (
        iSparrow.sparrow_setup.SPARROW_MODELS / "google_perch" / "saved_model.pb"
    ).is_file()
    assert (iSparrow.sparrow_setup.SPARROW_CONFIG / "install.yml").is_file()
    assert (iSparrow.sparrow_setup.SPARROW_CONFIG / "default.yml").is_file()
