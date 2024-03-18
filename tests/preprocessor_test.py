import pytest
from pathlib import Path
from birdnetlib import exceptions as ble
import numpy as np
from numpy.testing import assert_array_almost_equal


def test_preprocessor_constructions_birdnet(preprocessor_fx):
    preprocessor, _, _, _, _ = preprocessor_fx
    assert preprocessor.sample_rate == 48000
    assert preprocessor.overlap == pytest.approx(0.0)
    assert preprocessor.sample_secs == pytest.approx(3.0)
    assert preprocessor.resample_type == "kaiser_fast"
    assert preprocessor.duration == 0  # unknown at this point, hence zero
    assert preprocessor.actual_sampling_rate == pytest.approx(
        0.0
    )  # unknown at this point, hence zero
    assert preprocessor.name == "birdnet_defaults_preprocessor"


def test_preprocessor_read_birdnet(preprocessor_fx):
    preprocessor, cfg, _, filepath, _ = preprocessor_fx

    audiodata = preprocessor.read_audio_data(filepath)

    assert len(audiodata) == pytest.approx(
        preprocessor.actual_sampling_rate * preprocessor.duration
    )
    assert preprocessor.actual_sampling_rate == 48000
    assert preprocessor.duration == pytest.approx(120.0)


def test_preprocessor_processing_birdnet(preprocessor_fx):

    # use trimmed audio file that's not a multiple of 3s in length
    preprocessor, _, _, _, trimmedpath = preprocessor_fx

    recording_fx = preprocessor.read_audio_data(trimmedpath)

    chunks = preprocessor.process_audio_data(recording_fx)

    assert len(chunks) == pytest.approx(
        120.0 / 3.0
    )  # duration divided by sample_secs. last chunk is padded to 3

    # last chunks should have zeros in it for sampling_rate * 1.5
    # 72000 = (sampling_rate*duration)/2 = 1.5 seconds = last chunk that should be padded with zeros
    assert_array_almost_equal(chunks[-1][72000::], np.zeros(72000))


def test_preprocessor_constructions_google(preprocessor_fx_google):
    preprocessor, _, _, _, _ = preprocessor_fx_google
    assert preprocessor.sample_rate == 32000
    assert preprocessor.overlap == pytest.approx(0.0)
    assert preprocessor.sample_secs == pytest.approx(5.0)
    assert preprocessor.resample_type == "kaiser_fast"
    assert preprocessor.duration == 0  # unknown at this point, hence zero
    assert preprocessor.actual_sampling_rate == pytest.approx(
        0.0
    )  # unknown at this point, hence zero
    assert preprocessor.name == "google_perch"


def test_preprocessor_read_google(preprocessor_fx_google):
    preprocessor, cfg, _, filepath, _ = preprocessor_fx_google

    audiodata = preprocessor.read_audio_data(filepath)

    assert len(audiodata) == pytest.approx(
        preprocessor.actual_sampling_rate * preprocessor.duration
    )
    assert preprocessor.actual_sampling_rate == 32000
    assert preprocessor.duration == pytest.approx(120.0)


def test_preprocessor_processing_google(preprocessor_fx_google):

    preprocessor, _, _, _, trimmedpath = preprocessor_fx_google

    recording_fx = preprocessor.read_audio_data(trimmedpath)

    chunks = preprocessor.process_audio_data(recording_fx)

    assert len(chunks) == pytest.approx(
        120.0 / 5.0
    )  # duration divided by sample_secs. last chunk is padded to 5

    assert sum([len(chunk) for chunk in chunks]) == 120 * 32000

    # last chunk is only 3.5s, and must hence be padded with zeros to 5s
    # => (5 - 1.5)*sample_rate(=32000) = 1.5*32000 = 48000
    assert_array_almost_equal(chunks[-1][len(chunks[-1]) - 48000 : :], np.zeros(48000))


# README: no exception test because every OS throws a different exception...
