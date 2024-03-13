# import pytest
# from src.iSparrow import sparrow_analyzer as spa
# from birdnetlib.analyzer import AnalyzerConfigurationError


# def test_analyzer_construction_default(analyzer_fx):
#     tv = analyzer_fx

#     analyzer = spa.analyzer_from_config(tv.default_cfg["Analyzer"])

#     assert analyzer.apply_sigmoid is True
#     assert analyzer.sigmoid_sensitivity == 1.0
#     assert analyzer.num_threads == 12
#     assert analyzer.classifier_model_path is None
#     assert analyzer.classifier_labels_path is None
#     assert analyzer.default_model_path == "models/birdnet_defaults/model.tflite"
#     assert analyzer.default_labels_path == "models/birdnet_defaults/labels.txt"


# def test_analyzer_construction_missing_nodes(analyzer_fx):
#     tv = analyzer_fx

#     analyzer = spa.analyzer_from_config(tv.cfg_missing["Analyzer"])

#     assert analyzer.apply_sigmoid is True
#     assert analyzer.sigmoid_sensitivity == 1.0
#     assert analyzer.num_threads == 1
#     assert analyzer.classifier_model_path is None
#     assert analyzer.classifier_labels_path is None
#     assert analyzer.default_model_path == "models/birdnet_defaults/model.tflite"
#     assert analyzer.default_labels_path == "models/birdnet_defaults/labels.txt"


# def test_analyzer_custom_model(analyzer_fx):
#     tv = analyzer_fx

#     analyzer = spa.analyzer_from_config(tv.cfg["Analyzer"])

#     assert analyzer.apply_sigmoid is True
#     assert analyzer.sigmoid_sensitivity == 1.0
#     assert analyzer.num_threads == 12
#     assert analyzer.classifier_model_path == "models/birdnet_custom/model.tflite"
#     assert analyzer.classifier_labels_path == "models/birdnet_custom/labels.txt"
#     assert analyzer.default_model_path == "models/birdnet_defaults/model.tflite"
#     assert analyzer.default_labels_path == "models/birdnet_defaults/labels.txt"


# def test_analyzer_wrong_custom_model(analyzer_fx):
#     tv = analyzer_fx
#     with pytest.raises(AnalyzerConfigurationError) as exc_info:
#         spa.analyzer_from_config(tv.cfg_wrong_model["Analyzer"])

#     assert (
#         str(exc_info.value)
#         == "Custom classifier model could not be found at the provided path"
#     )


# def test_analyzer_wrong_custom_specieslist(analyzer_fx):
    
#     tv = analyzer_fx

#     with pytest.raises(AnalyzerConfigurationError) as exc_info:
#         spa.analyzer_from_config(tv.cfg_wrong_species_list["Analyzer"])

#     assert (
#         str(exc_info.value)
#         == "Custom species list path does not exist"
#     )


# def test_analyzer_correct_custom_specieslist(analyzer_fx):
    
#     tv = analyzer_fx

#     analyzer = spa.analyzer_from_config(tv.cfg_species_list["Analyzer"])
#     assert analyzer.has_custom_species_list is True
#     assert analyzer.custom_species_list[0] == "Cyanocitta cristata_Blue Jay"