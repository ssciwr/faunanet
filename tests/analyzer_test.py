import pytest
from src.iSparrow import sparrow_analyzer as spa
from birdnetlib.analyzer import AnalyzerConfigurationError


def test_analyzer_construction_default(analyzer_fx):
    tv = analyzer_fx

    analyzer = spa.SparrowAnalyzer(tv.default_cfg["Analyzer"])

    assert analyzer.apply_sigmoid is True
    assert analyzer.sigmoid_sensitivity == 1.0
    assert analyzer.num_threads == 12
    assert analyzer.classifier_model_path is None
    assert analyzer.classifier_labels_path is None
    assert analyzer.default_model_path == "models/birdnet_defaults/model.tflite"
    assert analyzer.default_labels_path == "models/birdnet_defaults/labels.txt"


def test_analyzer_construction_missing_nodes(analyzer_fx):
    tv = analyzer_fx

    analyzer = spa.SparrowAnalyzer(tv.cfg_missing["Analyzer"])

    assert analyzer.apply_sigmoid is True
    assert analyzer.sigmoid_sensitivity == 1.0
    assert analyzer.num_threads == 1
    assert analyzer.classifier_model_path is None
    assert analyzer.classifier_labels_path is None
    assert analyzer.default_model_path == "models/birdnet_defaults/model.tflite"
    assert analyzer.default_labels_path == "models/birdnet_defaults/labels.txt"


def test_analyzer_custom_model(analyzer_fx):
    tv = analyzer_fx

    analyzer = spa.SparrowAnalyzer(tv.cfg["Analyzer"])

    assert analyzer.apply_sigmoid is True
    assert analyzer.sigmoid_sensitivity == 1.0
    assert analyzer.num_threads == 12
    assert analyzer.classifier_model_path == "models/birdnet_custom/model.tflite"
    assert analyzer.classifier_labels_path == "models/birdnet_custom/labels.txt"
    assert analyzer.default_model_path == "models/birdnet_defaults/model.tflite"
    assert analyzer.default_labels_path == "models/birdnet_defaults/labels.txt"


def test_analyzer_excetptions(analyzer_fx):
    tv = analyzer_fx
    with pytest.raises(AnalyzerConfigurationError) as exc_info:
        spa.SparrowAnalyzer(tv.cfg_wrong["Analyzer"])

    assert (
        str(exc_info.value)
        == "Custom classifier model could not be found at the provided path"
    )
