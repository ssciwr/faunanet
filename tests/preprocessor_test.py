import pytest
from pathlib import Path
from birdnetlib import exceptions as ble
import numpy as np
from numpy.testing import assert_array_almost_equal


def test_preprocessor_constructions(preprocessor_fx):
    preprocessor, cfg, test_path, filepath, trimmedpath = preprocessor_fx
    assert preprocessor.sample_rate == 48000
    assert preprocessor.overlap == pytest.approx(0.0)
    assert preprocessor.sample_secs == pytest.approx(3.0)
    assert preprocessor.resample_type == "kaiser_fast"
    assert preprocessor.duration == 0  # unknown at this point, hence zero
    assert preprocessor.actual_sampling_rate == pytest.approx(
        0.0
    )  # unknown at this point, hence zero
    assert preprocessor.name == "birdnet_defaults_preprocessor"


def test_preprocessor_readind(preprocessor_fx):
    preprocessor, cfg, test_path, filepath, trimmedpath = preprocessor_fx

    audiodata = preprocessor.read_audio_data(filepath)

    assert len(audiodata) == pytest.approx(
        preprocessor.actual_sampling_rate * preprocessor.duration
    )
    assert preprocessor.actual_sampling_rate == 48000
    assert preprocessor.duration == pytest.approx(120.0)


def test_processing_processing(preprocessor_fx):

    # use trimmed audio file that's not a multiple of 3s in length
    preprocessor, cfg, test_path, filepath, trimmedpath = preprocessor_fx

    recording_fx = preprocessor.read_audio_data(trimmedpath)

    chunks = preprocessor.process_audio_data(recording_fx)

    assert len(chunks) == pytest.approx(
        120.0 / 3.0
    )  # duration divided by sample_secs. last chunk is padded to 3

    # last chunks should have zeros in it for sampling_rate * 1.5
    # 72000 = (sampling_rate*duration)/2 = 1.5 seconds = last chunk that should be padded with zeros
    assert_array_almost_equal(chunks[-1][72000::], np.zeros(72000))


def test_preprocessor_exceptions(preprocessor_fx):
    preprocessor, cfg, datapath, filepath, trimmedpath = preprocessor_fx

    with pytest.raises(FileNotFoundError) as exc_info:
        preprocessor.read_audio_data(
            datapath / Path("soundscape.mp12")
        )  # unknown format

    assert (
        str(exc_info.value)
        == "[Errno 2] No such file or directory: "
        + "'"
        + str(datapath / Path("soundscape.mp12"))
        + "'"
    )

    # read corrupted file --> Audio exception
    with pytest.raises(ble.AudioFormatError) as exc_info:
        preprocessor.read_audio_data(datapath / Path("corrupted.wav"))

    assert str(exc_info.value) == "Audio format could not be opened."
