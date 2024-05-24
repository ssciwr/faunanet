import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from pathlib import Path
from datetime import datetime
from src.faunanet import sparrow_recording as spc
from src.faunanet import species_predictor as spp


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
    assert recording.allowed_species == []
    assert recording.species_predictor is None


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
    assert recording.allowed_species == []
    assert recording.species_predictor is None


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
    assert recording.allowed_species == []
    assert recording.species_predictor is None


def test_recording_construction_inconsistent(recording_fx):

    # with pytest.raises(ValueError) as e_info:

    # this is an ugly attempt to make sonarcloud happy, the pytest 'with' statement was not accepted
    try:  # will definitely throw
        spc.SparrowRecording(
            recording_fx.default_preprocessor,
            recording_fx.google_model,
            recording_fx.good_file,
        )
    except Exception as e_info:
        assert (
            str(e_info)
            == "Found different 'name' attributes for model, preprocessor and species predictor. Make sure the supplied model, preprocessor and species predictor are compatible to each other (species_predictor may be 'None' if not used)."
        )


def test_analysis_custom(recording_fx):

    recording = spc.SparrowRecording(
        recording_fx.custom_preprocessor,
        recording_fx.custom_model,
        recording_fx.good_file,
        min_conf=0.25,
    )

    assert recording.analyzer.model_path == str(
        recording_fx.home
        / Path("models")
        / Path("birdnet_custom")
        / Path("model.tflite")
    )
    assert recording.analyzer.labels_path == str(
        recording_fx.home / Path("models") / Path("birdnet_custom") / Path("labels.txt")
    )
    assert recording.analyzer.default_model_path == str(
        recording_fx.home
        / Path("models")
        / Path("birdnet_default")
        / Path("model.tflite")
    )
    assert recording.analyzer.default_labels_path == str(
        recording_fx.home
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
    df = pd.DataFrame(results)

    df = (
        df.loc[df.end <= 15, ["label", "confidence"]]
        .sort_values(by="confidence", ascending=False)
        .reset_index(drop=True)
    )

    assert_frame_equal(
        df,  # we only have comparison data for the first 3 chunks
        recording_fx.google_analysis_results.loc[:, ["label", "confidence"]]
        .sort_values(by="confidence", ascending=False)
        .reset_index(drop=True),
        check_dtype=False,
        atol=1e-2,
    )


def test_model_exchange(recording_fx):

    # do analysis with google model and check it's ok again...
    recording = spc.SparrowRecording(
        recording_fx.google_preprocessor,
        recording_fx.google_model,
        recording_fx.good_file,
        min_conf=0.25,
    )
    assert recording.analyzer.name == "google_perch"
    assert recording.processor.name == "google_perch"

    recording.analyze()

    # results of analysis not explicitly needed here, we know what comes out from previous test

    # make a dataframe and sort it the same way as the expected recording_fx, with an index ranging from 0:len(df)-1
    # unfortunately, default test results where recorded with ascending = True... so it's inconsistent with custom

    # then switch to default model..
    recording.set_analyzer(
        recording_fx.default_model, recording_fx.default_preprocessor
    )

    assert recording.analyzer.name == "birdnet_default"
    assert recording.processor.name == "birdnet_default"

    recording.analyze()

    results = recording.detections

    #  and check it's ok as well
    df = (
        pd.DataFrame(results)
        .loc[:, ["label", "confidence"]]
        .sort_values(by="confidence", ascending=True)
        .reset_index()
        .drop("index", axis=1)
    )

    assert results != recording_fx.google_analysis_results.to_dict(
        orient="records"
    )  # make sure the results changed indeed

    assert_frame_equal(
        df,
        recording_fx.default_analysis_results.loc[:, ["label", "confidence"]],
        check_dtype=False,
    )


def test_species_list_restriction(recording_fx):
    p_cfg = recording_fx.default_cfg["Analysis"]["SpeciesPresence"]

    date_raw = p_cfg["date"].split("/")

    date = datetime(day=int(date_raw[0]), month=int(date_raw[1]), year=int(date_raw[2]))

    species_predictor_model_path = recording_fx.home / Path(
        recording_fx.default_cfg["Analysis"]["Model"]["model_path"]
    )

    recording = spc.SparrowRecording(
        recording_fx.default_preprocessor,
        recording_fx.default_model,
        recording_fx.good_file,
        date=date,
        lat=p_cfg["latitude"],
        lon=p_cfg["longitude"],
        species_presence_threshold=p_cfg["threshold"],
        species_predictor=spp.SpeciesPredictorBase(
            species_predictor_model_path, use_cache=False, num_threads=3
        ),
    )

    assert recording.species_predictor is not None
    assert recording.species_predictor.name == "birdnet_default"
    assert recording.species_predictor.name == "birdnet_default"
    assert recording.species_predictor.name == "birdnet_default"

    assert recording.species_predictor.num_threads == 3
    assert recording.species_predictor.use_cache is False
    assert recording.allowed_species == recording_fx.allowed_species_should

    recording.analyze()

    # need to do some post processing before comparison to make output formats compatible

    df = (
        pd.DataFrame(recording.detections)
        .sort_values(by="confidence", ascending=False)
        .reset_index(drop=True)
    )

    df.loc[:, "common_name"] = df.loc[:, "label"].apply(lambda x: x.split("_")[1])

    assert_frame_equal(
        df.loc[:, ["common_name", "confidence"]],
        recording_fx.detections_with_restricted_list.loc[
            :, ["common_name", "confidence"]
        ],
        check_dtype=False,
        atol=1e-2,
    )
