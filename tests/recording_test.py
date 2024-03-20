import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from pathlib import Path
from src.iSparrow import sparrow_recording as spc


def test_recording_construction_default(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.default_preprocessor,
        recording_fx.default_model,
        recording_fx.good_file,
    )

    assert recording.path == recording_fx.example_folder / Path("soundscape.wav")
    assert recording.filename == "soundscape.wav"
    assert recording.filestem == "soundscape"
    assert recording.chunks == []
    assert recording.minimum_confidence == pytest.approx(0.25)


def test_recording_construction_custom(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.custom_preprocessor,
        recording_fx.custom_model,
        recording_fx.good_file,
    )

    assert recording.path == recording_fx.example_folder / Path("soundscape.wav")
    assert recording.filename == "soundscape.wav"
    assert recording.filestem == "soundscape"
    assert recording.chunks == []
    assert recording.minimum_confidence == pytest.approx(0.25)


def test_recording_construction_google(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.google_preprocessor,
        recording_fx.google_model,
        recording_fx.good_file,
    )

    assert recording.path == recording_fx.example_folder / Path("soundscape.wav")
    assert recording.filename == "soundscape.wav"
    assert recording.filestem == "soundscape"
    assert recording.chunks == []
    assert recording.minimum_confidence == pytest.approx(0.25)


def test_analysis_custom(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.custom_preprocessor,
        recording_fx.custom_model,
        recording_fx.good_file,
        min_conf=0.25,
    )

    assert recording.model.model_path == str(
        recording_fx.sparrow_folder
        / Path("models")
        / Path("birdnet_custom")
        / Path("model.tflite")
    )
    assert recording.model.labels_path == str(
        recording_fx.sparrow_folder
        / Path("models")
        / Path("birdnet_custom")
        / Path("labels.txt")
    )
    assert recording.model.default_model_path == str(
        recording_fx.sparrow_folder
        / Path("models")
        / Path("birdnet_default")
        / Path("model.tflite")
    )
    assert recording.model.default_labels_path == str(
        recording_fx.sparrow_folder
        / Path("models")
        / Path("birdnet_default")
        / Path("labels.txt")
    )

    recording.analyze()

    results = recording.detections

    # make a dataframe and sort it the same way as the expected recording_fx, with an index ranging from 0:len(df)-1
    df = (
        pd.DataFrame(results)
        .loc[:, ["label", "confidence"]]
        .sort_values(by="confidence", ascending=False)
        .reset_index()
        .drop("index", axis=1)
    )

    assert_frame_equal(
        df,
        recording_fx.custom_analysis_results.loc[:, ["label", "confidence"]],
        check_dtype=False,
    )


def test_analysis_default(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.default_preprocessor,
        recording_fx.default_model,
        recording_fx.good_file,
        min_conf=0.25,
    )

    recording.analyze()
    results = recording.detections

    # make a dataframe and sort it the same way as the expected recording_fx, with an index ranging from 0:len(df)-1
    # unfortunately, default test results where recorded with ascending = True... so it's inconsistent with custom
    df = (
        pd.DataFrame(results)
        .loc[:, ["label", "confidence"]]
        .sort_values(by="confidence", ascending=True)
        .reset_index()
        .drop("index", axis=1)
    )

    assert_frame_equal(
        df,
        recording_fx.default_analysis_results.loc[:, ["label", "confidence"]],
        check_dtype=False,
    )


def test_analysis_google(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.google_preprocessor,
        recording_fx.google_model,
        recording_fx.good_file,
        min_conf=0.25,
    )

    recording.analyze()
    results = recording.detections

    # make a dataframe and sort it the same way as the expected recording_fx, with an index ranging from 0:len(df)-1
    # unfortunately, default test results where recorded with ascending = True... so it's inconsistent with custom
    df = (
        pd.DataFrame(results)
        .sort_values(by="confidence", ascending=False)
        .reset_index()
        .drop("index", axis=1)
    )

    print(
        df,
        "\n",
        recording_fx.google_analysis_results.loc[
            :, ["label", "confidence", "SCI_NAME"]
        ].sort_values(by="confidence", ascending=False),
    )

    assert_frame_equal(
        df.loc[:, ["label", "confidence"]],
        recording_fx.google_analysis_results.loc[:, ["label", "confidence"]],
        check_dtype=False,
    )
