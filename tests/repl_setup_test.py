import pytest
from pathlib import Path
import iSparrow
from .conftest import path_redirects


@pytest.fixture(autouse=True)
def redirect_folders(tmp_path, mocker):
    yield path_redirects(tmp_path, mocker)


def test_do_set_up(clean_up_test_installation, redirect_folders):
    filepath = Path(__file__).parent / "test_install_config" / "install.yml"
    cfg = iSparrow.utils.read_yaml(filepath)["Directories"]

    sparrow_cmd = iSparrow.repl.SparrowCmd()
    sparrow_cmd.do_set_up(
        f"--cfg={Path(__file__).parent}/test_install_config/install.yml"
    )

    tflite_file = "model.tflite"

    assert Path(cfg["home"]).expanduser().exists() is True
    assert Path(cfg["models"]).expanduser().exists() is True
    assert Path(cfg["output"]).expanduser().exists() is True

    assert (
        Path(cfg["models"]).expanduser() / "birdnet_default" / tflite_file
    ).is_file()
    assert (
        Path(cfg["models"]).expanduser() / "birdnet_custom" / tflite_file
    ).is_file()
    assert (
        Path(cfg["models"]).expanduser() / "google_perch" / "saved_model.pb"
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
def test_do_set_up_failure(input, expected, mocker, capsys, redirect_folders):
    capsys.readouterr()

    sparrow_cmd = iSparrow.repl.SparrowCmd()
    sparrow_cmd.do_set_up(input)
    out, _ = capsys.readouterr()
    assert expected in out
    capsys.readouterr()


def test_do_set_up_setup_exception(mocker, capsys, clean_up_test_installation, redirect_folders):
    mocker.patch(
        "iSparrow.sparrow_setup.set_up_sparrow", side_effect=Exception("RuntimeError")
    )
    sparrow_cmd = iSparrow.repl.SparrowCmd()
    sparrow_cmd.do_set_up("--cfg=./tests/test_configs")
    out, _ = capsys.readouterr()
    assert out == "Could not set up iSparrow RuntimeError caused by:  None\n"
    capsys.readouterr()
