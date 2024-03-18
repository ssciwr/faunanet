import pytest
import pandas as pd
import operator
from birdnetlib.analyzer import AnalyzerConfigurationError
from pathlib import Path
from pandas.testing import assert_frame_equal

def test_default_model_construction(model_fx):
    mfx = model_fx

    model = mfx.default_module.Model.from_cfg(
        mfx.sparrow_folder, mfx.default_cfg["Analyzer"]["Model"]
    )

    assert model.model_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("birdnet_default")
        / "model.tflite"
    )
    assert model.labels_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("birdnet_default")
        / "labels.txt"
    )
    assert model.sensitivity == pytest.approx(1.0)
    assert model.input_layer_index == 0
    assert model.output_layer_index == 546  # last


def test_custom_model_construction(model_fx):
    mfx = model_fx

    model = mfx.custom_module.Model.from_cfg(
        mfx.sparrow_folder, mfx.custom_cfg["Analyzer"]["Model"]
    )

    assert model.default_model_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("birdnet_default")
        / "model.tflite"
    )
    assert model.default_labels_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("birdnet_default")
        / "labels.txt"
    )

    assert model.model_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("birdnet_custom")
        / "model.tflite"
    )
    assert model.labels_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("birdnet_custom")
        / "labels.txt"
    )

    assert model.sensitivity == pytest.approx(1.0)
    assert model.input_layer_index == 0
    assert model.output_layer_index == 545  # second to last


def test_google_model_construction(model_fx):
    mfx = model_fx

    model = mfx.google_module.Model.from_cfg(
        mfx.sparrow_folder, mfx.google_cfg["Analyzer"]["Model"]
    )

    assert model.model_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("google_perch")
        / "saved_model.pb"
    )

    assert model.labels_path == str(
        Path.home()
        / Path("iSparrow")
        / Path("models")
        / Path("google_perch")
        / "labels.txt"
    )


def test_default_model_predict(model_fx):
    mfx = model_fx

    model = mfx.default_module.Model.from_cfg(
        mfx.sparrow_folder, mfx.default_cfg["Analyzer"]["Model"]
    )

    final_results = []
    for segment in mfx.data_default:

        results = model.predict(segment)[0]

        results = dict(zip(model.labels, results))

        p_sorted = list(
            sorted(results.items(), key=operator.itemgetter(1), reverse=True)
        )

        # Filter by recording.minimum_confidence so not to needlessly store full 8K array for each chunk.
        p_sorted = [i for i in p_sorted if i[1] >= 0.25]

        final_results.extend(p_sorted)

    # TODO: make this better/more thorough
    assert final_results[0][0] == "Abroscopus schisticeps_Black-faced Warbler"
    assert final_results[0][1] == pytest.approx(0.99999964)


def test_custom_model_predict(model_fx):
    mfx = model_fx

    model = mfx.custom_module.Model.from_cfg(
        mfx.sparrow_folder, mfx.custom_cfg["Analyzer"]["Model"]
    )

    final_results = []
    for segment in mfx.data_default:
        results = model.predict(segment)[0]

        results = dict(zip(model.labels, results))

        p_sorted = sorted(results.items(), key=operator.itemgetter(1), reverse=True)

        # Filter by recording.minimum_confidence so not to needlessly store full 8K array for each chunk.
        p_sorted = [i for i in p_sorted if i[1] >= 0.25]
        final_results.extend(p_sorted)

    print(final_results[0])
    # TODO: check that this is actually different from the default (if it actually is)
    assert final_results[0][0] == "Poecile atricapillus_Black-capped Chickadee"
    assert final_results[0][1] == pytest.approx(0.95653343)


def test_google_model_predict(model_fx):
    mfx = model_fx

    model = mfx.google_module.Model.from_cfg(
        mfx.sparrow_folder, mfx.google_cfg["Analyzer"]["Model"]
    )

    final_results = []
    for chunk in mfx.data_google:

        results = model.predict(chunk)

        results = results.sort_values(by="probabilities", ascending=False)

        final_results.append(results)

    final_results = pd.concat(final_results)

    print(final_results.loc[:, ["scientific_name", "probabilities"]])
    assert final_results["scientific_name"].iloc[0] == "Poecile carolinensis"
    assert final_results["probabilities"].iloc[0] == pytest.approx(0.5022050)
    assert final_results["scientific_name"].iloc[1] == "Poecile weigoldicus"
    assert final_results["probabilities"].iloc[1] == pytest.approx(0.1517491)
