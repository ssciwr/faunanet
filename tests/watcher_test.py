import pytest
from pathlib import Path
from iSparrow import SparrowWatcher
from datetime import datetime
from copy import deepcopy


def test_event_handler_creation(watch_fx):
    pass


def test_watcher_construction(watch_fx, install):
    wfx = watch_fx

    path_add = Path(datetime.now().strftime("%y%m%d_%H%M%S"))
    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    config_should = {
        "Analysis": {
            "input": str(Path.home() / Path("iSparrow_data")),
            "output": str(Path.home() / Path("iSparrow_output") / path_add),
            "model_dir": str(Path.home() / "iSparrow/models"),
            "Preprocessor": deepcopy(wfx.preprocessor_cfg),
            "Model": model_cfg,
            "Recording": deepcopy(wfx.recording_cfg),
            "SpeciesPredictor": deepcopy(wfx.species_predictor_cfg),
        }
    }

    watcher = SparrowWatcher(
        Path.home() / "iSparrow_data",
        Path.home() / "iSparrow_output",
        Path.home() / "iSparrow/models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    assert str(watcher.output) == str(Path(watcher.outdir) / path_add)
    assert str(watcher.input) == str(Path.home() / "iSparrow_data")
    assert str(watcher.outdir) == str(Path.home() / "iSparrow_output")
    assert str(watcher.model_dir) == str(Path.home() / "iSparrow/models")
    assert str(watcher.model_name) == "birdnet_default"
    assert watcher.output_directory == str(Path(watcher.outdir) / path_add)
    assert watcher.input_directory == str(Path.home() / "iSparrow_data")
    assert watcher.is_running is False
    assert watcher.output.is_dir() is False  # not yet created
    assert watcher.input.is_dir()
    assert watcher.outdir.is_dir()
    assert watcher.model_dir.is_dir()
    assert (watcher.model_dir / watcher.model_name).is_dir()
    assert watcher.config == config_should
    assert watcher.pattern == ".wav"
    assert watcher.check_time == 1
    assert watcher.recording.processor.name == "birdnet_default"
    assert watcher.recording.analyzer.name == "birdnet_default"
    assert watcher.recording.species_predictor.name == "birdnet_default"
    assert Path(watcher.output / "config.yml").is_file()
    assert len(watcher.recording.allowed_species) > 0
    assert watcher.delete_recordings == "on_cleanup"
    assert watcher.recording is not None
    assert watcher.model_name == "birdnet_default"
    assert watcher.preprocessor_name == "birdnet_default"
    assert watcher.species_presence_model_name == "birdnet_default"

    # give wrong paths and check that appropriate exceptions are raised
    with pytest.raises(ValueError, match="Input directory does not exist"):
        SparrowWatcher(
            Path.home() / "iSparrow_data_not_there",
            Path.home() / "iSparrow_output",
            Path.home() / "iSparrow/models",
            "birdnet_default",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(ValueError, match="Output directory does not exist"):
        SparrowWatcher(
            Path.home() / "iSparrow_data",
            Path.home() / "iSparrow_output_not_there",
            Path.home() / "iSparrow/models",
            "birdnet_default",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(ValueError, match="Model directory does not exist"):
        SparrowWatcher(
            Path.home() / "iSparrow_data",
            Path.home() / "iSparrow_output",
            Path.home() / "iSparrow/models_not_there",
            "birdnet_default",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(
        ValueError, match="Given model name does not exist in model directory"
    ):
        SparrowWatcher(
            Path.home() / "iSparrow_data",
            Path.home() / "iSparrow_output",
            Path.home() / "iSparrow/models",
            "does_not_exist",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(
        ValueError,
        match="An error occured during species range predictor creation. Does you model provide a model file called 'species_presence_model'?",
    ):
        SparrowWatcher(
            Path.home() / "iSparrow_data",
            Path.home() / "iSparrow_output",
            Path.home() / "iSparrow/models",
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(
        ValueError,
        match="'delete_recordings' must be in 'never', 'on_cleanup', 'always'",
    ):
        SparrowWatcher(
            Path.home() / "iSparrow_data",
            Path.home() / "iSparrow_output",
            Path.home() / "iSparrow/models",
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
            delete_recordings="some wrong value",
        )

    watcher = SparrowWatcher(
        Path.home() / "iSparrow_data",
        Path.home() / "iSparrow_output",
        Path.home() / "iSparrow/models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg_unrestricted),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    assert watcher.species_presence_model_name == "no species predictor present"
    assert watcher.recording.species_predictor is None


def test_watcher_lowlevel_functionality(watch_fx, folders, install):
    wfx = watch_fx
    home, data, output = folders

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    watcher = SparrowWatcher(
        Path.home() / "iSparrow_data",
        Path.home() / "iSparrow_output",
        Path.home() / "iSparrow/models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    watcher.analyze(
        home / "example" / "soundscape.wav",
    )

    assert len(list(output.iterdir())) == 1
    datafolder = list(output.iterdir())[0]

    assert len(list(datafolder.iterdir())) == 2
    assert list(datafolder.iterdir()) == [
        datafolder / "config.yml",
        Path(datafolder / "results_soundscape.csv"),
    ]

    assert watcher.recording.analyzed is True
    assert watcher.recording.path == home / "example" / "soundscape.wav"
    assert len(watcher.recording.allowed_species) > 0
    assert watcher.recording.species_predictor is not None
    assert len(watcher.recording.analyzer.results) > 0
    assert len(watcher.recording.analyzer.results) > len(
        watcher.current_results
    )  # current results is filtered

    # run the watcher process dry and make sure start, pause stop works
    watcher.start()
    assert watcher.wait_event.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True
    assert watcher.watcher_process.name == "watcher_process"

    watcher.pause()
    assert watcher.wait_event.is_set() is False
    assert watcher.is_running is True

    watcher.go_on()
    assert watcher.wait_event.is_set() is True
    assert watcher.is_running is True

    watcher.stop()
    assert watcher.is_running is False
    assert watcher.exit_ok == 0
