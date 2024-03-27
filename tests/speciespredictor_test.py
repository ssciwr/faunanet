from iSparrow import species_predictor as sp

from pathlib import Path
import yaml
import pytest
from datetime import datetime
import pandas as pd

# README: the species predictor in its current form only runs with the default model.
# Therefore, no tests are performed with any other model.
# Once a custom species predictor is supplied, these need to be added.


@pytest.fixture(scope="module")
def finalizer():
    sp.SpeciesPredictorBase.clear_cache()


def test_species_predictor_construction(recording_fx, finalizer):
    with open(
        recording_fx.testpath / Path("test_configs") / "cfg_default.yml", "r"
    ) as cfgfile:
        cfg = yaml.safe_load(cfgfile)

    model_path = str(
        Path(recording_fx.models_folder) / cfg["Analysis"]["Model"]["model_path"]
    )

    labels_path = str(
        recording_fx.models_folder
        / cfg["Analysis"]["Model"]["model_path"]
        / "labels.txt"
    )

    p_cfg = cfg["Analysis"]["SpeciesPresence"]

    predictor = sp.SpeciesPredictorBase(
        model_path,
        use_cache=p_cfg["use_cache"],
        num_threads=p_cfg["num_threads"],
    )

    assert predictor.name == "birdnet_default"

    assert predictor.model_path == str(
        Path(model_path) / "species_presence_model.tflite"
    )

    assert predictor.labels_path == labels_path

    assert predictor.use_cache is True

    assert predictor.num_threads == 2

    assert predictor.meta_interpreter is not None

    assert predictor.meta_input_layer_index == 0

    assert predictor.meta_output_layer_index == 81

    assert predictor.read_from_file is False

    model_path = str(Path(recording_fx.models_folder) / "model_that_doesn't exist")

    with pytest.raises(FileNotFoundError) as e_info:
        predictor = sp.SpeciesPredictorBase(
            model_path,
            use_cache=p_cfg["use_cache"],
            num_threads=p_cfg["num_threads"],
        )

    assert (
        str(e_info.value)
        == "The model folder for the species presenece predictor could not be found"
    )

    assert Path(predictor.cache_dir).exists()


def test_species_predictor_run(recording_fx, finalizer):

    with open(
        recording_fx.testpath / Path("test_configs") / "cfg_default.yml", "r"
    ) as cfgfile:
        cfg = yaml.safe_load(cfgfile)

    detections_should = (
        pd.read_csv(
            recording_fx.testpath
            / Path("stored_test_results")
            / Path("species_list.txt"),
            comment="#",
            header=None,
        )
        .squeeze()
        .tolist()
    )

    model_path = str(
        Path(recording_fx.models_folder) / cfg["Analysis"]["Model"]["model_path"]
    )

    p_cfg = cfg["Analysis"]["SpeciesPresence"]

    p_cfg["use_cache"] = False

    predictor = sp.SpeciesPredictorBase(
        model_path,
        use_cache=p_cfg["use_cache"],
        num_threads=p_cfg["num_threads"],
    )

    assert predictor.read_from_file is False

    date_raw = p_cfg["date"].split("/")

    date = datetime(day=int(date_raw[0]), month=int(date_raw[1]), year=int(date_raw[2]))

    detections = predictor.predict(
        p_cfg["latitude"], p_cfg["longitude"], date=date, threshold=p_cfg["threshold"]
    )

    assert detections == detections_should

    assert predictor.read_from_file is False


def test_cached_species_predictor_run(recording_fx, finalizer):

    # make a species list using the cache, then make sure it is present in the cache folder

    with open(
        recording_fx.testpath / Path("test_configs") / "cfg_default.yml", "r"
    ) as cfgfile:
        cfg = yaml.safe_load(cfgfile)

    model_path = str(
        Path(recording_fx.models_folder) / cfg["Analysis"]["Model"]["model_path"]
    )

    p_cfg = cfg["Analysis"]["SpeciesPresence"]

    predictor = sp.SpeciesPredictorBase(
        model_path,
        use_cache=True,
        num_threads=p_cfg["num_threads"],
    )

    # just use some random date
    date = datetime(day=10, month=6, year=2022)

    lat = 40.5  # use some different coordinates

    lon = -74.25  # use some different coordinates

    detections = predictor.predict(lat, lon, date=date, threshold=p_cfg["threshold"])

    assert predictor.read_from_file is False

    assert (
        Path(predictor.cache_dir) / Path("40.5_-74.25_22") / "species_list.txt"
    ).is_file()

    read_detections = predictor.predict(
        lat, lon, date=date, threshold=p_cfg["threshold"]
    )

    assert predictor.read_from_file

    assert detections == read_detections
