import pytest
import pandas as pd
import operator
from birdnetlib.analyzer import AnalyzerConfigurationError
from pathlib import Path
from pandas.testing import assert_frame_equal

pd.set_option("display.max_columns", None)


def test_default_model_construction(model_fx):
    mfx = model_fx

    model = mfx.default_module.Model.from_cfg(
        mfx.home, mfx.default_cfg["Analysis"]["Model"]
    )

    assert model.model_path == str(
        mfx.models_folder / Path("birdnet_default") / "model.tflite"
    )
    assert model.labels_path == str(
        mfx.models_folder / Path("birdnet_default") / "labels.txt"
    )
    assert model.sensitivity == pytest.approx(1.0)
    assert model.input_layer_index == 0
    assert model.output_layer_index == 546  # last
    assert model.name == "birdnet_default"


def test_custom_model_construction(model_fx):
    mfx = model_fx

    model = mfx.custom_module.Model.from_cfg(
        mfx.home, mfx.custom_cfg["Analysis"]["Model"]
    )

    assert model.default_model_path == str(
        mfx.models_folder / Path("birdnet_default") / "model.tflite"
    )
    assert model.default_labels_path == str(
        mfx.models_folder / Path("birdnet_default") / "labels.txt"
    )

    assert model.model_path == str(
        mfx.models_folder / Path("birdnet_custom") / "model.tflite"
    )
    assert model.labels_path == str(
        mfx.models_folder / Path("birdnet_custom") / "labels.txt"
    )

    assert model.sensitivity == pytest.approx(1.0)
    assert model.input_layer_index == 0
    assert model.output_layer_index == 545  # second to last
    assert model.name == "birdnet_custom"


def test_google_model_construction(model_fx):
    mfx = model_fx

    model = mfx.google_module.Model.from_cfg(
        mfx.home, mfx.google_cfg["Analysis"]["Model"]
    )

    assert model.model_path == str(
        mfx.models_folder / Path("google_perch") / "saved_model.pb"
    )

    assert model.labels_path == str(
        mfx.models_folder / Path("google_perch") / "labels.txt"
    )

    assert model.sensitivity == pytest.approx(1.0)
    assert model.name == "google_perch"


def test_default_model_predict(model_fx):
    mfx = model_fx

    model = mfx.default_module.Model.from_cfg(
        mfx.home, mfx.default_cfg["Analysis"]["Model"]
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

    df = pd.DataFrame(
        final_results, columns=["scientific_name", "confidence"]
    ).sort_values(by="confidence", ascending=False)

    # remove common name from label
    df.loc[:, "scientific_name"] = df["scientific_name"].apply(
        lambda x: x.split("_")[0]
    )

    # assert that results are equivalent to the previous once/the ones obtained with birdnet-Analysis
    assert_frame_equal(
        df.reset_index(drop=True),
        mfx.default_analysis_results.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        atol=1e-2,
    )


def test_custom_model_predict(model_fx):
    mfx = model_fx

    model = mfx.custom_module.Model.from_cfg(
        mfx.home, mfx.custom_cfg["Analysis"]["Model"]
    )

    final_results = []
    for segment in mfx.data_default:
        results = model.predict(segment)[0]

        results = dict(zip(model.labels, results))

        p_sorted = sorted(results.items(), key=operator.itemgetter(1), reverse=True)

        # Filter by recording.minimum_confidence so not to needlessly store full 8K array for each chunk.
        p_sorted = [i for i in p_sorted if i[1] >= 0.25]
        final_results.extend(p_sorted)

    df = pd.DataFrame(
        final_results, columns=["scientific_name", "confidence"]
    ).sort_values(by="confidence", ascending=False)

    # remove common name from label
    df.loc[:, "scientific_name"] = df["scientific_name"].apply(
        lambda x: x.split("_")[0]
    )

    # assert that results are equivalent to the previous once/the ones obtained with birdnet-Analysis
    assert_frame_equal(
        df.reset_index(drop=True),
        mfx.custom_analysis_results.reset_index(drop=True),
        check_dtype=False,
        check_exact=False,
        atol=1e-2,
    )


def test_google_model_predict(model_fx):
    mfx = model_fx

    model = mfx.google_module.Model.from_cfg(
        mfx.home, mfx.google_cfg["Analysis"]["Model"]
    )

    final_results = []
    for chunk in mfx.data_google[0:3]:  # use only the first 3 chunks to limit runtime

        results = model.predict(chunk)[0]

        results = list(zip(model.labels, results))

        final_results.extend(results)

    final_results = (
        pd.DataFrame(final_results, columns=["labels", "confidence"])
        .sort_values(by="confidence", ascending=False)
        .reset_index(drop=True)
    )

    final_results = final_results.loc[final_results.confidence >= 0.25, :]

    assert_frame_equal(
        final_results,
        model_fx.google_result.loc[:, ["labels", "confidence"]],
        check_dtype=False,
        check_exact=False,
        atol=1e-2,
    )
