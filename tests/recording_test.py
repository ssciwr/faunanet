import sys
import yaml
import pytest
import numpy as np
from numpy.testing import assert_array_equal
import importlib

from pathlib import Path

sys.path.append('../src/iSparrow')
from src.iSparrow import sparrow_recording as spc
from src.iSparrow import sparrow_analyzer as spa


@pytest.fixture
def recorded_data():
    tests = Path(__file__).resolve().parent
    home = tests.parent
    with open(tests / Path("example") / "test.yml", "r") as file:
        cfg = yaml.safe_load(file)

    pp = importlib.import_module('models.' + cfg["Analyzer"]["Model"]["path"]+'.preprocessor')

    preprocessor = pp.Preprocessor(cfg["Data"]["Preprocessor"])
    analyzer = spa.SparrowAnalyzer(cfg["Analyzer"])
    recording = spc.SparrowRecording(analyzer, preprocessor, tests / "example/soundscape.wav")
    return recording, tests, home


def test_recording_construction(recorded_data):
    recording, testpath, homepath = recorded_data

    assert recording.path == testpath / Path("example/soundscape.wav")
    assert recording.filename == "soundscape.wav"
    assert recording.filestem == "soundscape"
    assert recording.chunks == []

    assert recording.processor.sample_rate == 48000
    assert recording.processor.overlap == pytest.approx(0.0)
    assert recording.processor.sample_secs == pytest.approx(3.0)
    assert recording.processor.resample_type == 'kaiser_fast'
    assert recording.processor.duration == 0  # unknown at this point, hence zero
    assert recording.processor.actual_sampling_rate == pytest.approx(0.)  # unknown at this point, hence zero


def test_recording_reading(recorded_data):

    recording, testpath, homepath = recorded_data
    data = recording.processor.read_audio_data(testpath / Path("example/soundscape.wav"))

    assert len(data) == pytest.approx(recording.processor.actual_sampling_rate * recording.processor.duration)
    assert recording.processor.actual_sampling_rate == 48000
    assert recording.processor.duration == pytest.approx(120.0)


def test_recording_processing(recorded_data):

    recording, testpath, homepath = recorded_data
    # use trimmed audio file that's not a multiple of 3s in length

    data = recording.processor.read_audio_data(testpath / Path("example/trimmed.wav"))

    chunks = recording.processor.process_audio_data(data)

    assert len(chunks) == pytest.approx(120.0 / 3.0)  # duration divided by sample_secs. last chunk is padded to 3

    # last chunks should have zeros in it for sampling_rate * 1.5
    # 72000 = (sampling_rate*duration)/2 = 1.5 seconds = last chunk that should be padded with zeros
    assert_array_equal(chunks[-1][72000::], np.zeros(72000))


def test_analysis(recorded_data):
    assert 3 == 3