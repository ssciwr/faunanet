import pytest
import pathlib
import shutil
import platformdirs
import iSparrow
import time


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
    assert iSparrow.repl.process_line_into_kwargs(
        "--cfg=./tests/test_configs --stuff=other", keywords=["cfg", "stuff"]
    ) == {"cfg": "./tests/test_configs", "stuff": "other"}

    with pytest.raises(
        ValueError, match="Invalid input. Expected options structure is --name=<arg>"
    ):
        iSparrow.repl.process_line_into_kwargs(
            "./tests/test_configs",
            keywords=[
                "cfg",
            ],
        )

    with pytest.raises(ValueError, match="Keywords must be provided with passed line"):
        iSparrow.repl.process_line_into_kwargs("--cfg=./tests/test_configs")

    assert iSparrow.repl.process_line_into_kwargs("") == {}


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
def test_process_line_into_kwargs_failures(input, keywords, message):
    with pytest.raises(ValueError, match=message):
        iSparrow.repl.process_line_into_kwargs(input, keywords=keywords)


def test_do_set_up(clean_up_test_installation):
    filepath =  pathlib.Path(__file__).parent / "test_install_config" / "install.yml"
    cfg = iSparrow.utils.read_yaml(filepath)["Directories"]

    sparrow_cmd = iSparrow.repl.SparrowCmd()
    sparrow_cmd.do_set_up(f"--cfg={pathlib.Path(__file__).parent}/test_install_config/install.yml")

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

    sparrow_cmd = iSparrow.repl.SparrowCmd()
    sparrow_cmd.do_set_up(input)
    out, _ = capsys.readouterr()
    assert expected in out
    capsys.readouterr()


def test_do_set_up_setup_exception(mocker, capsys, clean_up_test_installation):
    mocker.patch(
        "iSparrow.sparrow_setup.set_up_sparrow", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = iSparrow.repl.SparrowCmd()
    sparrow_cmd.do_set_up("--cfg=./tests/test_configs")
    out, _ = capsys.readouterr()
    assert out == "Could not set up iSparrow RuntimeError caused by:  None\n"
    capsys.readouterr()
