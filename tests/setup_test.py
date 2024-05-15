import iSparrow.sparrow_setup as sps
from pathlib import Path
import pytest
import shutil
from .conftest import path_redirects

tflite_file = "model.tflite"

@pytest.fixture(autouse=True)
def redirect_folders(tmp_path, mocker):
    yield path_redirects(tmp_path, mocker)


@pytest.fixture()
def make_folders(redirect_folders):
    temp_dir = redirect_folders
    for path in [
        "test_models",
        "test_examples",
        "test_cache",
    ]:
        Path(temp_dir, path).mkdir(parents=True, exist_ok=True)

    yield

    for path in [
        "test_models",
        "test_examples",
        "test_cache",
    ]:
        shutil.rmtree(Path(temp_dir, path))


def test_make_directories(tmp_path):
    base_cfg_dirs = {
        "home": str(Path(tmp_path, "test_home")),
        "models": str(Path(tmp_path, "test_models")),
        "output": str(Path(tmp_path, "test_output")),
    }

    folders = sps.make_directories(base_cfg_dirs)
    for folder in folders:
        assert folder.exists()

    for path in folders:
        if path.exists():
            shutil.rmtree(path)


def test_make_directories_exceptions():
    base_cfg_dirs = {"models": "test_models", "output": "test_output"}

    with pytest.raises(
        KeyError, match="The home folder for iSparrow must be given in the base config"
    ):
        sps.make_directories(base_cfg_dirs)

    base_cfg_dirs = {"home": "test_home", "output": "test_output"}

    with pytest.raises(
        KeyError,
        match="The models folder for iSparrow must be given in the base config",
    ):
        sps.make_directories(base_cfg_dirs)

    base_cfg_dirs = {
        "home": "test_home",
        "models": "test_models",
    }

    with pytest.raises(
        KeyError,
        match="The output folder for iSparrow must be given in the base config",
    ):
        sps.make_directories(base_cfg_dirs)


def test_download_example_data(tmp_path, make_folders):
    example_dir = str(Path(tmp_path, "test_examples"))

    sps.download_example_data(example_dir)

    assert Path(example_dir).exists()
    assert Path(example_dir, "soundscape.wav").is_file()
    assert Path(example_dir, "corrupted.wav").is_file()
    assert Path(example_dir, "trimmed.wav").is_file()
    assert Path(example_dir, "species_list.txt").is_file()


def test_download_example_data_exceptions(make_folders):
    example_dir = "test_examples_nonexistent"
    with pytest.raises(
        FileNotFoundError, match="The folder test_examples_nonexistent does not exist"
    ):
        sps.download_example_data(example_dir)


def test_download_model_files(tmp_path, make_folders):
    model_dir = str(Path(tmp_path, "test_models"))
    sps.download_model_files(model_dir)
    assert Path(model_dir).exists()
    assert Path(model_dir, "birdnet_default", tflite_file).is_file()
    assert Path(model_dir, "birdnet_custom", tflite_file).is_file()
    assert Path(model_dir, "google_perch", "saved_model.pb").is_file()


def test_download_model_files_exceptions(make_folders):
    model_dir = "test_models_nonexistent"
    with pytest.raises(
        FileNotFoundError, match="The folder test_models_nonexistent does not exist"
    ):
        sps.download_model_files(model_dir)


def test_setup(clean_up_test_installation):
    filepath = Path(__file__).parent / "test_install_config" / "install.yml"

    sps.set_up_sparrow(filepath)

    assert sps.SPARROW_HOME.exists()
    assert sps.SPARROW_EXAMPLES.exists()
    assert sps.SPARROW_MODELS.exists()
    assert sps.SPARROW_OUTPUT.exists()
    assert sps.SPARROW_CONFIG.exists()
    assert sps.SPARROW_CACHE.exists()

    assert (
        sps.SPARROW_MODELS / "birdnet_default" / tflite_file
    ).is_file()
    assert (
        sps.SPARROW_MODELS / "birdnet_custom" / tflite_file
    ).is_file()
    assert (
        sps.SPARROW_MODELS / "google_perch" / "saved_model.pb"
    ).is_file()
    assert (sps.SPARROW_CONFIG / "install.yml").is_file()
    assert (sps.SPARROW_CONFIG / "default.yml").is_file()
