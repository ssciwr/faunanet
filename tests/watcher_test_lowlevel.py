import pytest
from pathlib import Path
from iSparrow.sparrow_watcher import AnalysisEventHandler
from iSparrow import SparrowWatcher
from copy import deepcopy
import yaml
from math import isclose


def test_watcher_construction(watch_fx):
    wfx = watch_fx

    watcher = SparrowWatcher(
        wfx.data,
        wfx.output,
        wfx.home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    # check member variables
    assert str(watcher.output) == str(Path(watcher.outdir) / wfx.path_add)
    assert str(watcher.input) == str(Path.home() / "iSparrow_data")
    assert str(watcher.outdir) == str(Path.home() / "iSparrow_output")
    assert str(watcher.model_dir) == str(Path.home() / "iSparrow/models")
    assert str(watcher.model_name) == "birdnet_default"
    assert watcher.output_directory == str(Path(watcher.outdir) / wfx.path_add)
    assert watcher.input_directory == str(Path.home() / "iSparrow_data")
    assert watcher.is_running is False
    assert watcher.output.is_dir() is False  # not yet created
    assert watcher.input.is_dir()
    assert watcher.outdir.is_dir()
    assert watcher.model_dir.is_dir()
    assert (watcher.model_dir / watcher.model_name).is_dir()
    assert watcher.pattern == ".wav"
    assert watcher.check_time == 1
    assert watcher.delete_recordings == "on_cleanup"
    assert watcher.model_name == "birdnet_default"

    watcher.output.mkdir(exist_ok=True, parents=True)

    watcher._write_config()

    with open(watcher.output / "config.yml", "r") as cfgfile:
        config = yaml.safe_load(cfgfile)

    assert config == wfx.config_should

    recording = watcher.set_up_recording()

    assert recording.analyzer.name == "birdnet_default"
    assert recording.path == ""
    assert recording.processor.name == "birdnet_default"
    assert recording.species_predictor.name == "birdnet_default"
    assert len(recording.allowed_species) > 0
    assert recording.species_predictor is not None
    assert isclose(recording.minimum_confidence, 0.25)
    assert isclose(recording.sensitivity, 1.0)

    # give wrong paths and check that appropriate exceptions are raised
    with pytest.raises(ValueError, match="Input directory does not exist"):
        SparrowWatcher(
            Path.home() / "iSparrow_data_not_there",
            wfx.output,
            wfx.home / "models",
            "birdnet_default",
        )

    with pytest.raises(ValueError, match="Output directory does not exist"):
        SparrowWatcher(
            wfx.data,
            Path.home() / "iSparrow_output_not_there",
            wfx.home / "/models",
            "birdnet_default",
        )

    with pytest.raises(ValueError, match="Model directory does not exist"):
        SparrowWatcher(
            wfx.data,
            wfx.output,
            wfx.home / "models_not_there",
            "birdnet_default",
        )

    with pytest.raises(
        ValueError, match="Given model name does not exist in model directory"
    ):
        SparrowWatcher(
            wfx.data,
            wfx.output,
            wfx.home / "models",
            "does_not_exist",
        )

    with pytest.raises(
        ValueError,
        match="An error occured during species range predictor creation. Does you model provide a model file called 'species_presence_model'?",
    ):
        sp = SparrowWatcher(
            wfx.data,
            wfx.output,
            wfx.home / "models",
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
        )

        sp.set_up_recording()

    with pytest.raises(
        ValueError,
        match="'delete_recordings' must be in 'never', 'on_cleanup', 'always'",
    ):
        SparrowWatcher(
            wfx.data,
            wfx.output,
            wfx.home / "models",
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            delete_recordings="some wrong value",
        )


def test_event_handler_construction(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher()

    event_handler = AnalysisEventHandler(
        watcher,
    )

    assert event_handler.pattern == ".wav"
    assert event_handler.recording.analyzer.name == "birdnet_default"
    assert event_handler.recording.processor.name == "birdnet_default"
    assert event_handler.recording.species_predictor.name == "birdnet_default"
    assert event_handler.callback == watcher.analyze


def test_watcher_lowlevel_functionality(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher()

    recording = watcher.set_up_recording()

    # this is normally performed by the `start` method of the watcher,
    # but because this is a low level test of the basic functionality
    # we must do it by hand here:
    watcher.output.mkdir(parents=True, exist_ok=True)

    watcher.may_do_work.set()

    # ... now we can call the functions to be tested

    watcher.analyze(wfx.home / "example" / "soundscape.wav", recording)

    assert len(list(wfx.output.iterdir())) == 1
    datafolder = list(wfx.output.iterdir())[0]

    assert len(list(datafolder.iterdir())) == 1
    assert list(datafolder.iterdir()) == [
        Path(datafolder / "results_soundscape.csv"),
    ]

    assert recording.analyzed is True
    assert recording.path == wfx.home / "example" / "soundscape.wav"
    assert len(recording.allowed_species) > 0
    assert recording.species_predictor is not None
    assert len(recording.analyzer.results) > 0


def test_watcher_daemon_lowlevel_functionality(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher()

    # this is normally performed by the `start` method of the watcher,
    # but because this is a low level test of the basic functionality
    # we must do it by hand here:
    watcher.output.mkdir(parents=True, exist_ok=True)
    # run the watcher process dry and make sure start, pause stop works
    watcher.start()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True
    assert watcher.watcher_process.name == "watcher_process"

    # artificially set the finish event flag because no data is there
    watcher.is_done_analyzing.set()
    watcher.pause()
    assert watcher.may_do_work.is_set() is False
    assert watcher.is_running is True
    assert watcher.is_done_analyzing.is_set() is True

    watcher.go_on()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True

    with pytest.raises(
        RuntimeError, match="watcher process still running, stop first."
    ):
        watcher.start()

    # artificially set the finish flag because we have no data to work with
    watcher.stop()
    assert watcher.is_running is False
    assert watcher.watcher_process is None
    assert watcher.may_do_work.is_set() is False
    assert watcher.is_done_analyzing.is_set() is True

    with pytest.raises(
        RuntimeError, match="Cannot continue watcher process, is not alive anymore."
    ):
        watcher.go_on()

    with pytest.raises(
        RuntimeError, match="Cannot stop watcher process, is not alive anymore."
    ):
        watcher.stop()

    with pytest.raises(
        RuntimeError, match="Cannot pause watcher process, is not alive anymore."
    ):
        watcher.pause()

    watcher.recording_cfg = wfx.recording_cfg  # necessary because it will be modified
    watcher.start()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True

    # artificially set finish flag because no data is there
    watcher.recording_cfg = wfx.recording_cfg  # necessary because it will be modified
    watcher.is_done_analyzing.set()
    watcher.restart()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True
