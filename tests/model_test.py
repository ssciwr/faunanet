import pytest

from birdnetlib.analyzer import AnalyzerConfigurationError
from pathlib import Path


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
    assert model.output_layer_index == 546
