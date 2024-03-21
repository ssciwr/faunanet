import sys

sys.path.append("../src/iSparrow")
from src.iSparrow import utils
from src.iSparrow import species_predictor as sp

from pathlib import Path
import yaml

# README: the species predictor in its current form only runs with the default model.
# Therefore, no tests are performed with any other model.
# Once a custom species predictor is supplied, these need to be added.


def species_predictor_construction_test(fx):
    with open(fx.testpath / Path("test_configs") / "cfg_default.yml", "r") as cfgfile:
        cfg = yaml.safe_load(cfgfile)

    model_path = str(
        fx.models_folder
        / cfg["Analysis"]["Model"]["model_path"]
        / "species_presence_model.tflite"
    )

    labels_path = str(
        fx.models_folder / cfg["Analysis"]["Model"]["model_path"] / "labels.txt"
    )

    p_cfg = cfg["Analysis"]["SpeciesPresence"]

    predictor = sp.SpeciesPredictorBase(
        model_path,
        use_cache=p_cfg["use_cache"],
        threshold=p_cfg["threshold"],
        num_threads=p_cfg["num_threads"],
    )

    assert predictor.model_path == model_path

    assert predictor.labels_path == labels_path

    assert predictor.use_cache == True

    assert predictor.threshold == 0.3

    assert predictor.num_threads == 2

    assert predictor.meta_interpreter is not None

    assert predictor.meta_input_layer_index == 0

    assert predictor.meta_output_layer_index == 2


def species_predictor_run_test():
    assert 3 == 3


def species_predictor_run_test_cached():
    assert 3 == 3
