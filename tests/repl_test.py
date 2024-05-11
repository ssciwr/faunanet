import pytest

from iSparrow.repl import SparrowCmd, process_line_into_kwargs
from iSparrow.utils import read_yaml
from importlib.resources import files
from pathlib import Path
import shutil
from platformdirs import user_cache_dir, user_config_dir

from iSparrow.sparrow_setup import download_example_data, download_model_files


@pytest.fixture()
def make_test_setup():
    cfg = read_yaml("./tests/test_install_config/install.yml")["Directories"]
    for name, path in cfg.items():
        Path(path).expanduser().mkdir(parents=True, exist_ok=True)

    iscfg = Path(user_config_dir()) / "iSparrow_tests"
    iscache = Path(user_cache_dir()) / "iSparrow_tests"

    iscfg.mkdir(parents=True, exist_ok=True)
    iscache.mkdir(parents=True, exist_ok=True)

    ism = Path(cfg["models"]).expanduser()
    ise = Path(cfg["home"]).expanduser() / "example"
    ise.mkdir(parents=True, exist_ok=True)

    download_model_files(ism)
    download_example_data(ise)
    import iSparrow
    packagebase = files(iSparrow)
    shutil.copy(packagebase / "install.yml", iscfg)
    shutil.copy(packagebase / "default.yml", iscfg)

    yield

    for name, path in cfg.items():
        shutil.rmtree(Path(path).expanduser(), ignore_errors=True)


@pytest.fixture()
def delete_folders_again():
    yield

    cfg = read_yaml("./tests/test_install_config/install.yml")["Directories"]

    for name in ["home", "output", "data"]:
        shutil.rmtree(Path(cfg[name]).expanduser(), ignore_errors=True)


def test_process_line_into_kwargs():
    assert process_line_into_kwargs(
        "--cfg=./tests/test_configs --stuff=other", keywords=["cfg", "stuff"]
    ) == {"cfg": "./tests/test_configs", "stuff": "other"}

    with pytest.raises(
        ValueError, match="Invalid input. Expected options structure is --name=<arg>"
    ):
        process_line_into_kwargs(
            "./tests/test_configs",
            keywords=[
                "cfg",
            ],
        )

    with pytest.raises(ValueError, match="Keywords must be provided with passed line"):
        process_line_into_kwargs("--cfg=./tests/test_configs")

    assert process_line_into_kwargs("") == {}


# def test_do_set_up(delete_folders_again):

#     cfg = read_yaml("./tests/test_install_config/install.yml")["Directories"]

#     sparrow_cmd = SparrowCmd()
#     sparrow_cmd.do_set_up("--cfg=./tests/test_install_config/install.yml")

#     tflite_file = "model.tflite"

#     assert Path(cfg["home"]).expanduser().exists() is True
#     assert Path(cfg["models"]).expanduser().exists() is True
#     assert Path(cfg["output"]).expanduser().exists() is True

#     assert (
#         Path(cfg["models"]).expanduser() / "birdnet_default" / tflite_file
#     ).is_file()
#     assert (Path(cfg["models"]).expanduser() / "birdnet_custom" / tflite_file).is_file()
#     assert (
#         Path(cfg["models"]).expanduser() / "google_perch" / "saved_model.pb"
#     ).is_file()


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            "--cfg./tests/test_configs",
            "Something in the setup command parsing went wrong. Check your passed commands. Caused by:  Invalid input. Expected options structure is --name=<arg>\n",
        ),
        (
            "--cfg=./tests/test_configs --stuff=superfluous",
            "Invalid input. Expected: set_up --cfg=<config_file>\n",
        ),
    ],
)
def test_do_set_up_args_error(input, expected, capsys):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_set_up(input)
    out, _ = capsys.readouterr()
    assert out == expected


def test_do_set_up_setup_error(mocker, capsys):
    mocker.patch(
        "iSparrow.sparrow_setup.set_up_sparrow", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_set_up("--cfg=./tests/test_configs")
    out, _ = capsys.readouterr()
    assert out == "Could not set up iSparrow RuntimeError caused by:  None\n"


def test_do_start_custom(make_test_setup):

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    assert sparrow_cmd.watcher is not None
    assert sparrow_cmd.watcher.outdir == Path.home() / "iSparrow_test_install_output"
    assert sparrow_cmd.watcher.input_directory == str(
        Path.home() / "iSparrow_test_install_data"
    )
    assert sparrow_cmd.watcher.model_dir == Path.home() / "iSparrow_test_install/models"
    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False
    assert sparrow_cmd.watcher.is_sleeping is False
    assert sparrow_cmd.watcher.delete_recordings == "always"
    assert sparrow_cmd.watcher.pattern == ".mp3"
    sparrow_cmd.watcher.stop()


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            "--cfg./tests/test_configs/watcher_custom.yml",
            "Something in the setup command parsing went wrong. Check your passed commands. Caused by:  Invalid input. Expected options structure is --name=<arg>\n",
        ),
        (
            "--cfg=./tests/test_configs/watcher_custom.yml --stuff=superfluous",
            "Invalid input. Expected: start --cfg=<config_file>\n",
        ),
    ],
)
def test_do_start_wrong_args(input, expected, capsys, mocker):
    mock_watcher = mocker.patch("iSparrow.repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start(input)
    out, _ = capsys.readouterr()
    assert out == expected


def test_do_stop(mocker):
    mock_watcher = mocker.patch("iSparrow.repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_stop("")
    mock_watcher_instance.stop.assert_called_once()


def test_do_pause(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_pause("")
    mock_watcher_instance.pause.assert_called_once()


def test_do_continue(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = True
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_continue("")
    mock_watcher_instance.go_on.assert_called_once()


def test_do_restart(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_restart("")
    mock_watcher_instance.restart.assert_called_once()


def test_do_exit(mocker):
    sparrow_cmd = SparrowCmd()
    assert sparrow_cmd.do_exit("") == True


def test_change_analyzer(mocker):
    mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
    mock_watcher_instance = mock_watcher.return_value
    mock_watcher_instance.is_running = True
    mock_watcher_instance.is_sleeping = False
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.change_analyzer("--cfg=test")
    mock_watcher_instance.change_analyzer.assert_called_once()


def test_process_line():
    assert process_line_into_kwargs("--cfg=test") == ["test"]
    assert process_line_into_kwargs("--cfg=test --cfg2=test2") == ["test", "test2"]
    assert process_line_into_kwargs("") == []
    assert process_line_into_kwargs("--cfg") is None
