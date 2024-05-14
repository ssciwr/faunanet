import pytest

from iSparrow.repl import SparrowCmd, process_line_into_kwargs
from iSparrow.utils import read_yaml
from iSparrow.sparrow_setup import download_example_data, download_model_files
import iSparrow

import pathlib
import shutil
import platformdirs
import time
from copy import deepcopy


@pytest.fixture()
def delete_setup(redirect_folders):
    cfg = read_yaml("./tests/test_install_config/install.yml")["Directories"]

    yield

    for name, path in cfg.items():
        shutil.rmtree(pathlib.Path(path).expanduser(), ignore_errors=True)

    shutil.rmtree(
        pathlib.Path(platformdirs.user_config_dir()) / "iSparrow", ignore_errors=True
    )
    shutil.rmtree(
        pathlib.Path(platformdirs.user_cache_dir()) / "iSparrow", ignore_errors=True
    )


@pytest.fixture()
def make_test_setup(delete_setup):
    cfg = read_yaml("./tests/test_install_config/install.yml")["Directories"]

    for name, path in cfg.items():
        pathlib.Path(path).expanduser().mkdir(parents=True, exist_ok=True)

    iscfg = pathlib.Path(platformdirs.user_config_dir()) / "iSparrow"
    iscache = pathlib.Path(platformdirs.user_cache_dir()) / "iSparrow"

    iscfg.mkdir(parents=True, exist_ok=True)
    iscache.mkdir(parents=True, exist_ok=True)

    ism = pathlib.Path(cfg["models"]).expanduser()
    ise = pathlib.Path(cfg["home"]).expanduser() / "example"
    ise.mkdir(parents=True, exist_ok=True)

    download_model_files(ism)
    download_example_data(ise)

    shutil.copy(pathlib.Path("tests", "test_install_config", "install.yml"), iscfg)
    shutil.copy(pathlib.Path("tests", "test_install_config", "default.yml"), iscfg)

    yield


def wait_on_watcher_startup(sparrow_cmd):
    i = 0
    while True:
        if i > 10:
            assert False
        if sparrow_cmd.watcher.is_running:
            break
        else:
            time.sleep(3)
            i += 1


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


@pytest.mark.parametrize(
    "input, keywords, message",
    [
        (
            "-no equality sign",
            [
                "cfg",
            ],
            "Invalid input. Expected options structure is --name=<arg>",
        ),
        (
            "--cfg=./tests/test_configs",
            [],
            "Keywords must be provided with passed line",
        ),
        (
            "--cfg=./tests/test_configs",
            None,
            "Keywords must be provided with passed line",
        ),
        (
            "--cfg=./tests/test_configs",
            [
                "rkg",
            ],
            "Keyword rkg not found in passed line",
        ),
    ],
)
def test_process_line_into_kwargs_failures(input, keywords, message, make_test_setup):
    with pytest.raises(ValueError, match=message):
        process_line_into_kwargs(input, keywords=keywords)


def test_do_set_up(delete_setup):

    cfg = read_yaml("./tests/test_install_config/install.yml")["Directories"]

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_set_up("--cfg=./tests/test_install_config/install.yml")

    tflite_file = "model.tflite"

    assert pathlib.Path(cfg["home"]).expanduser().resolve().exists() is True
    assert pathlib.Path(cfg["models"]).expanduser().resolve().exists() is True
    assert pathlib.Path(cfg["output"]).expanduser().resolve().exists() is True

    assert (
        pathlib.Path(cfg["models"]).expanduser().resolve()
        / "birdnet_default"
        / tflite_file
    ).is_file()
    assert (
        pathlib.Path(cfg["models"]).expanduser().resolve()
        / "birdnet_custom"
        / tflite_file
    ).is_file()
    assert (
        pathlib.Path(cfg["models"]).expanduser().resolve()
        / "google_perch"
        / "saved_model.pb"
    ).is_file()


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            "--cfg./tests/test_configs",
            "Could not set up iSparrow Invalid input. Expected options structure is --name=<arg> caused by:  None\n",
        ),
        (
            "--cfg=./tests/test_configs --stuff=superfluous",
            "Expected 1 blocks of the form --name=<arg>\n",
        ),
        ("", "No config file provided, falling back to default"),
    ],
)
def test_do_set_up_failure(input, expected, mocker, capsys):
    capsys.readouterr()

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_set_up(input)
    out, _ = capsys.readouterr()
    assert expected in out
    capsys.readouterr()


def test_do_set_up_setup_exception(mocker, capsys, delete_setup):
    mocker.patch(
        "iSparrow.sparrow_setup.set_up_sparrow", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_set_up("--cfg=./tests/test_configs")
    out, _ = capsys.readouterr()
    assert out == "Could not set up iSparrow RuntimeError caused by:  None\n"
    capsys.readouterr()


def test_do_start_custom(make_test_setup, capsys):

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    assert sparrow_cmd.watcher is not None
    assert sparrow_cmd.watcher.outdir == pathlib.Path.home() / "iSparrow_output"
    assert sparrow_cmd.watcher.input_directory == str(
        pathlib.Path.home() / "iSparrow_data"
    )
    assert sparrow_cmd.watcher.model_dir == pathlib.Path.home() / "iSparrow/models"
    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False
    assert sparrow_cmd.watcher.is_sleeping is False
    assert sparrow_cmd.watcher.delete_recordings == "always"
    assert sparrow_cmd.watcher.pattern == ".mp3"
    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False

    capsys.readouterr()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    out, _ = capsys.readouterr()
    assert sparrow_cmd.watcher.is_running is True
    assert (
        out
        == "It appears that there is a watcher process that is not running. Trying to start with current parameters. Use  the 'change_analyzer' command to change the parameters.\nstart the watcher process\n"
    )

    capsys.readouterr()
    sparrow_cmd.do_start("")
    out, _ = capsys.readouterr()
    assert (
        "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters.\n"
        in out
    )

    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False


@pytest.mark.parametrize(
    "input, expected, status",
    [
        (
            "--cfg./tests/test_configs/watcher_custom.yml",
            "Something in the start command parsing went wrong. Check your passed commands. Caused by:  Invalid input. Expected options structure is --name=<arg>\n",
            True,
        ),
        (
            "--cfg=./tests/test_configs/watcher_custom.yml --stuff=superfluous",
            "Invalid input. Expected 1 blocks of the form --name=<arg>\n",
            True,
        ),
        ("", "No config file provided, falling back to default", False),
    ],
)
def test_do_start_failure(input, expected, status, capsys, make_test_setup):
    capsys.readouterr()
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start(input)
    out, _ = capsys.readouterr()
    assert expected in out
    assert (sparrow_cmd.watcher is None) is status

    if sparrow_cmd.watcher is not None and sparrow_cmd.watcher.is_running is True:
        sparrow_cmd.watcher.stop()


def test_do_start_exception_in_watcher_start(make_test_setup, mocker, capsys):
    mocker.patch.object(
        iSparrow.SparrowWatcher, "start", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = SparrowCmd()

    capsys.readouterr()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    out, _ = capsys.readouterr()
    assert (
        out
        == "Something went wrong while trying to start the watcher: RuntimeError caused by  None. A new start attempt can be made when the error has been addressed.\n"
    )

    if sparrow_cmd.watcher is not None and sparrow_cmd.watcher.is_running is True:
        sparrow_cmd.watcher.stop()


def test_do_start_exception_in_watcher_build(make_test_setup, mocker, capsys):
    mocker.patch.object(
        iSparrow.SparrowWatcher, "__init__", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = SparrowCmd()
    capsys.readouterr()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    out, _ = capsys.readouterr()
    assert (
        out
        == "An error occured while trying to build the watcher: RuntimeError caused by None\n"
    )
    if sparrow_cmd.watcher is not None and sparrow_cmd.watcher.is_running is True:
        sparrow_cmd.watcher.stop()


def test_do_stop(make_test_setup):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    time.sleep(5)
    assert sparrow_cmd.watcher.is_running is True
    sparrow_cmd.do_stop("")
    assert sparrow_cmd.watcher.is_running is False


def test_do_stop_failure(make_test_setup, capsys):
    sparrow_cmd = SparrowCmd()

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)
    capsys.readouterr()
    sparrow_cmd.do_stop("something_wrong")
    out, _ = capsys.readouterr()
    assert "Invalid input. Expected no arguments." in out

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True
    sparrow_cmd.watcher.stop()
    capsys.readouterr()
    sparrow_cmd.do_stop("")
    out, _ = capsys.readouterr()
    assert out == "Cannot stop watcher, is not running\n"


def test_do_stop_exceptions(make_test_setup, capsys, mocker):
    mocker.patch("iSparrow.SparrowWatcher.stop", side_effect=Exception("RuntimeError"))

    sparrow_cmd = SparrowCmd()

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    capsys.readouterr()

    sparrow_cmd.do_stop("")

    out, _ = capsys.readouterr()
    assert (
        out
        == "Could not stop watcher: RuntimeError caused by None. Watcher process will be killed now and all resources released. This may have left data in a corrupt state. A new watcher must be started if this session is to be continued.\n"
    )

    if sparrow_cmd.watcher is not None and sparrow_cmd.watcher.is_running is True:
        sparrow_cmd.watcher.stop()


def test_do_pause(make_test_setup):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True
    # fake work done
    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_pause("")
    assert sparrow_cmd.watcher.is_sleeping is True
    assert sparrow_cmd.watcher.is_running is True
    sparrow_cmd.watcher.go_on()
    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False


def test_do_pause_failures(make_test_setup, capsys):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    assert sparrow_cmd.watcher.is_running is True
    time.sleep(5)
    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_pause("cfg=wrong_argument")
    out, _ = capsys.readouterr()
    assert "Invalid input. Expected no arguments.\n" in out

    sparrow_cmd.watcher.stop()
    i = 0
    while True:
        if i > 10:
            assert False
        if sparrow_cmd.watcher.is_running is False:
            break
        else:
            time.sleep(3)
            i += 1
    capsys.readouterr()
    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_pause("")
    out, _ = capsys.readouterr()
    assert out == "Cannot pause watcher, is not running\n"

    capsys.readouterr()
    sparrow_cmd.watcher = None
    sparrow_cmd.do_pause("")
    out, _ = capsys.readouterr()
    assert out == "Cannot pause watcher, no watcher present\n"

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.watcher.pause()

    capsys.readouterr()
    sparrow_cmd.do_pause("")
    out, _ = capsys.readouterr()
    assert out == "Cannot pause watcher, is already sleeping\n"


def test_do_pause_exception(make_test_setup, capsys, mocker):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    assert sparrow_cmd.watcher.is_running is True
    wait_on_watcher_startup(sparrow_cmd)

    mocker.patch("iSparrow.SparrowWatcher.pause", side_effect=Exception("RuntimeError"))
    sparrow_cmd.watcher.is_done_analyzing.set()
    capsys.readouterr()
    sparrow_cmd.do_pause("")
    out, _ = capsys.readouterr()
    assert out == "Could not pause watcher: RuntimeError caused by None\n"
    assert sparrow_cmd.watcher is not None
    assert sparrow_cmd.watcher.is_running is True

    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False


def test_do_continue(make_test_setup):

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    assert sparrow_cmd.watcher.is_running is True
    wait_on_watcher_startup(sparrow_cmd)

    # fake work done
    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_pause("")
    assert sparrow_cmd.watcher.is_sleeping is True
    assert sparrow_cmd.watcher.is_running is True
    sparrow_cmd.do_continue("")
    assert sparrow_cmd.watcher.is_sleeping is False
    assert sparrow_cmd.watcher.is_running is True
    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False


def test_do_continue_failure(make_test_setup, capsys):

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    assert sparrow_cmd.watcher.is_running is True

    wait_on_watcher_startup(sparrow_cmd)

    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_pause("")
    assert sparrow_cmd.watcher.is_sleeping is True
    assert sparrow_cmd.watcher.is_running is True

    capsys.readouterr()
    sparrow_cmd.do_continue("cfg=wrong_argument")
    out, _ = capsys.readouterr()
    assert "Invalid input. Expected no arguments.\n" in out

    sparrow_cmd.do_stop("")
    sparrow_cmd.watcher = None

    capsys.readouterr()
    assert sparrow_cmd.watcher is None

    sparrow_cmd.do_continue("")

    out, _ = capsys.readouterr()
    assert out == "Cannot continue watcher, no watcher present\n"

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    capsys.readouterr()
    sparrow_cmd.do_continue("")
    out, _ = capsys.readouterr()

    assert out == "Cannot continue watcher, is not sleeping\n"

    sparrow_cmd.watcher.stop()

    capsys.readouterr()
    sparrow_cmd.do_continue("")
    out, _ = capsys.readouterr()

    assert out == "Cannot continue watcher, is not running\n"


def test_do_continue_exception(make_test_setup, capsys, mocker):

    mocker.patch("iSparrow.SparrowWatcher.go_on", side_effect=Exception("RuntimeError"))

    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True

    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_pause("")
    assert sparrow_cmd.watcher.is_sleeping is True
    assert sparrow_cmd.watcher.is_running is True

    capsys.readouterr()
    sparrow_cmd.do_continue("")
    out, _ = capsys.readouterr()
    assert out == "Could not continue watcher: RuntimeError caused by None\n"


def test_do_restart(make_test_setup):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False
    old_output = deepcopy(sparrow_cmd.watcher.output)
    sparrow_cmd.do_restart("")
    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False
    assert old_output == sparrow_cmd.watcher.output
    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False


def test_do_restart_failure(make_test_setup, capsys):
    sparrow_cmd = SparrowCmd()

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False

    capsys.readouterr()
    sparrow_cmd.do_restart("wrong input")
    out, _ = capsys.readouterr()
    assert "Invalid input. Expected no arguments.\n" in out

    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.watcher.pause()

    capsys.readouterr()
    sparrow_cmd.do_restart("")
    out, _ = capsys.readouterr()
    assert "Cannot restart watcher, is sleeping and must be continued first\n" in out

    sparrow_cmd.watcher.stop()

    capsys.readouterr()
    sparrow_cmd.do_restart("")
    out, _ = capsys.readouterr()
    assert out == "Cannot restart watcher, is not running\n"


def test_do_restart_exceptions(make_test_setup, capsys, mocker):
    mocker.patch.object(
        iSparrow.SparrowWatcher, "stop", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = SparrowCmd()

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False

    capsys.readouterr()
    sparrow_cmd.do_restart("")
    out, _ = capsys.readouterr()
    assert (
        out
        == "trying to restart the watcher process\nCould not restart watcher: RuntimeError caused by None\n"
    )


def test_do_exit(capsys):
    sparrow_cmd = SparrowCmd()

    capsys.readouterr()
    sparrow_cmd.do_exit("wrong args")
    out, _ = capsys.readouterr()
    assert out == "Invalid input. Expected no arguments.\n"

    capsys.readouterr()

    value = sparrow_cmd.do_exit("")

    assert value is True

    out, _ = capsys.readouterr()

    assert out == "Exiting sparrow shell\n"


def test_change_analyzer(make_test_setup):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("")

    wait_on_watcher_startup(sparrow_cmd)

    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False
    time.sleep(10)
    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.do_change_analyzer("--cfg=./tests/test_configs/watcher_custom.yml")


def test_change_analyzer_exception(make_test_setup, capsys, mocker):
    mocker.patch.object(
        iSparrow.SparrowWatcher,
        "change_analyzer",
        side_effect=Exception("RuntimeError"),
    )

    sparrow_cmd = SparrowCmd()
    capsys.readouterr()
    sparrow_cmd.do_change_analyzer("")
    out, _ = capsys.readouterr()
    assert out == "No watcher present, cannot change analyzer\n"

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    sparrow_cmd.watcher.is_done_analyzing.set()

    capsys.readouterr()
    sparrow_cmd.do_change_analyzer("--cfg=./tests/test_configs/watcher_custom.yml")

    out, _ = capsys.readouterr()

    assert (
        out
        == "An error occured while trying to change the analyzer: RuntimeError caused by None\n"
    )

    if sparrow_cmd.watcher is not None and sparrow_cmd.watcher.is_running is True:
        sparrow_cmd.watcher.stop()


def test_change_analyzer_failure(make_test_setup, capsys):
    sparrow_cmd = SparrowCmd()
    capsys.readouterr()
    sparrow_cmd.do_change_analyzer("")
    out, _ = capsys.readouterr()
    assert out == "No watcher present, cannot change analyzer\n"

    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")

    wait_on_watcher_startup(sparrow_cmd)

    sparrow_cmd.watcher.is_done_analyzing.set()
    sparrow_cmd.watcher.pause()

    capsys.readouterr()
    sparrow_cmd.do_change_analyzer("--cfg=./tests/test_configs/watcher_custom.yml")
    out, _ = capsys.readouterr()
    assert out == "Cannot change analyzer, watcher is sleeping\n"

    sparrow_cmd.watcher.stop()
    capsys.readouterr()
    sparrow_cmd.do_change_analyzer("--cfg=./tests/test_configs/watcher_custom.yml")
    out, _ = capsys.readouterr()
    assert out == "Cannot change analyzer, watcher is not running\n"

    sparrow_cmd.watcher = None
    capsys.readouterr()
    sparrow_cmd.do_change_analyzer("--cfg=./tests/test_configs/watcher_custom.yml")
    out, _ = capsys.readouterr()
    assert out == "No watcher present, cannot change analyzer\n"


def test_do_check(make_test_setup, capsys):
    sparrow_cmd = SparrowCmd()
    sparrow_cmd.do_start("--cfg=./tests/test_configs/watcher_custom.yml")
    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False

    wait_on_watcher_startup(sparrow_cmd)

    capsys.readouterr()
    sparrow_cmd.do_check("")
    out, _ = capsys.readouterr()
    assert out == "is running: True\nis sleeping: False\nmay do work: True\n"
    assert sparrow_cmd.watcher.is_running is True
    assert sparrow_cmd.watcher.is_sleeping is False
    sparrow_cmd.watcher.stop()
    assert sparrow_cmd.watcher.is_running is False

    capsys.readouterr()
    sparrow_cmd.do_check("wrong input")
    out, _ = capsys.readouterr()
    assert out == "Invalid input. Expected no arguments.\n"

    sparrow_cmd.watcher = None

    capsys.readouterr()
    sparrow_cmd.do_check("")
    out, _ = capsys.readouterr()
    assert out == "No watcher present, cannot check status\n"
