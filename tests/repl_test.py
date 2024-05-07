import pytest
import iSparrow.repl
from iSparrow.repl import SparrowCmd, process_line_into_kwargs
from iSparrow import SparrowWatcher
from iSparrow.utils import read_yaml
from unittest.mock import Mock
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir


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


def test_do_set_up():
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_set_up("--cfg=./tests/test_configs")

    cfg = read_yaml("./tests/test_configs/install.yml")["Directories"]
    assert Path(cfg["home"]).expanduser().exists()
    assert Path(cfg["data"]).expanduser().exists()
    assert Path(cfg["models"]).expanduser().exists()
    assert Path(cfg["output"]).expanduser().exists()
    assert (Path(user_cache_dir()) / "iSparrow").exists()
    assert (Path(user_config_dir()) / "iSparrow").exists()
    assert (Path(user_config_dir()) / "iSparrow" / "install.yml").is_file()


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


def test_do_start_custom():
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    assert sparrow_cmd.watcher.input_directory == str(
        Path.home() / "iSparrow_tests_data"
    )
    assert sparrow_cmd.watcher.outdir == Path.home() / "iSparrow_tests_output"
    assert sparrow_cmd.watcher.model_dir == Path.home() / "iSparrow_tests/models"
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


# def test_do_stop(mocker):
#     mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
#     mock_watcher_instance = mock_watcher.return_value
#     mock_watcher_instance.is_running = True
#     sparrow_cmd = SparrowCmd()
#     sparrow_cmd.do_stop("")
#     mock_watcher_instance.stop.assert_called_once()


# def test_do_pause(mocker):
#     mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
#     mock_watcher_instance = mock_watcher.return_value
#     mock_watcher_instance.is_running = True
#     mock_watcher_instance.is_sleeping = False
#     sparrow_cmd = SparrowCmd()
#     sparrow_cmd.do_pause("")
#     mock_watcher_instance.pause.assert_called_once()


# def test_do_continue(mocker):
#     mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
#     mock_watcher_instance = mock_watcher.return_value
#     mock_watcher_instance.is_running = True
#     mock_watcher_instance.is_sleeping = True
#     sparrow_cmd = SparrowCmd()
#     sparrow_cmd.do_continue("")
#     mock_watcher_instance.go_on.assert_called_once()


# def test_do_restart(mocker):
#     mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
#     mock_watcher_instance = mock_watcher.return_value
#     mock_watcher_instance.is_running = True
#     mock_watcher_instance.is_sleeping = False
#     sparrow_cmd = SparrowCmd()
#     sparrow_cmd.do_restart("")
#     mock_watcher_instance.restart.assert_called_once()


# def test_do_exit(mocker):
#     sparrow_cmd = SparrowCmd()
#     assert sparrow_cmd.do_exit("") == True


# def test_change_analyzer(mocker):
#     mock_watcher = mocker.patch("repl.SparrowWatcher", autospec=True)
#     mock_watcher_instance = mock_watcher.return_value
#     mock_watcher_instance.is_running = True
#     mock_watcher_instance.is_sleeping = False
#     sparrow_cmd = SparrowCmd()
#     sparrow_cmd.change_analyzer("--cfg=test")
#     mock_watcher_instance.change_analyzer.assert_called_once()


# def test_process_line():
#     assert process_line("--cfg=test") == ["test"]
#     assert process_line("--cfg=test --cfg2=test2") == ["test", "test2"]
#     assert process_line("") == []
#     assert process_line("--cfg") == None
