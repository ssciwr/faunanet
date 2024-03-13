import pytest
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd
from pandas.testing import assert_frame_equal
from pathlib import Path
from copy import deepcopy
import importlib
from src.iSparrow import sparrow_recording as spc
from src.iSparrow import sparrow_analyzer as spa


def test_recording_construction(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.analyzer, recording_fx.preprocessor, recording_fx.good_file
    )

    assert recording.path == recording_fx.test_path / Path("example/soundscape.wav")
    assert recording.filename == "soundscape.wav"
    assert recording.filestem == "soundscape"
    assert recording.chunks == []
    assert recording.minimum_confidence == pytest.approx(0.25)

def test_analysis_custom(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.analyzer,
        recording_fx.preprocessor,
        recording_fx.good_file,
        min_conf=0.25,
    )

    assert recording.analyzer.classifier_model_path == str(
        Path("models") / Path("birdnet_custom") / Path("model.tflite")
    )
    assert recording.analyzer.classifier_labels_path == str(
        Path("models") / Path("birdnet_custom") / Path("labels.txt")
    )
    assert recording.analyzer.use_custom_classifier is not False
    assert recording.analyzer.default_model_path == str(
        Path("models") / Path("birdnet_defaults") / Path("model.tflite")
    )
    assert recording.analyzer.default_labels_path == str(
        Path("models") / Path("birdnet_defaults") / Path("labels.txt")
    )

    recording.analyze()

    # make a dataframe and sort it the same way as the expected recording_fx, with an index ranging from 0:len(df)-1
    df = (
        pd.DataFrame(recording.detections)
        .sort_values(by="confidence", ascending=False)
        .reset_index()
        .drop("index", axis=1)
    )

    assert_frame_equal(df, recording_fx.custom_analysis_results)


def test_analysis_default(recording_fx):

    default_cfg = deepcopy(recording_fx.cfg)

    default_cfg["Analyzer"]["Model"]["model_name"] = "birdnet_defaults"
    ppd = importlib.import_module(
        "models." + default_cfg["Analyzer"]["Model"]["model_name"] + ".preprocessor"
    )

    default_analyzer = spa.SparrowAnalyzer(default_cfg["Analyzer"])
    default_preprocessor = ppd.Preprocessor(default_cfg["Data"]["Preprocessor"])

    recording = spc.SparrowRecording(
        default_analyzer, default_preprocessor, recording_fx.good_file, min_conf=0.25
    )

    assert recording.analyzer.classifier_model_path is None
    assert recording.analyzer.classifier_labels_path is None
    assert recording.analyzer.use_custom_classifier is None
    assert recording.analyzer.default_model_path == str(
        Path("models") / Path("birdnet_defaults") / Path("model.tflite")
    )
    assert recording.analyzer.default_labels_path == str(
        Path("models") / Path("birdnet_defaults") / Path("labels.txt")
    )

    recording.analyze()

    # make a dataframe and sort it the same way as the expected recording_fx, with an index ranging from 0:len(df)-1
    # unfortunately, default test results where recorded with ascending = True... so it's inconsistent with custom
    df = (
        pd.DataFrame(recording.detections)
        .sort_values(by="confidence", ascending=True)
        .reset_index()
        .drop("index", axis=1)
    )
    assert_frame_equal(df, recording_fx.default_analysis_results)
