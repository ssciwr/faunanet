import pytest
from pathlib import Path
from birdnetlib import exceptions as ble


def test_recording_preprocessor_exceptions(wrong_paths_fx):
    preprocessor, cfg, testpath = wrong_paths_fx

    with pytest.raises(FileNotFoundError) as exc_info:
        preprocessor.read_audio_data(
            testpath / Path("example") / Path("soundscape.mp12")
        )  # unknown format

    assert (
        str(exc_info.value)
        == "[Errno 2] No such file or directory: "
        + "'"
        + str(testpath / Path("example") / Path("soundscape.mp12"))
        + "'"
    )

    # read corrupted file --> Audio exception
    with pytest.raises(ble.AudioFormatError) as exc_info:
        preprocessor.read_audio_data(testpath / Path("example") / Path("corrupted.wav"))

    assert str(exc_info.value) == "Audio format could not be opened."
