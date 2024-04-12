import pytest
from pathlib import Path
from iSparrow import SparrowWatcher
from iSparrow.utils import wait_for_file_completion
from datetime import datetime
from copy import deepcopy
import shutil
import multiprocessing
import yaml
import time
import pandas as pd


def test_event_handler_creation(watch_fx):
    pass


def test_watcher_construction(watch_fx, install, folders):
    wfx = watch_fx
    home, data, output = folders

    path_add = Path(datetime.now().strftime("%y%m%d_%H%M%S"))
    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    config_should = {
        "Analysis": {
            "input": str(data),
            "output": str(output / path_add),
            "model_dir": str(home / "models"),
            "Preprocessor": deepcopy(wfx.preprocessor_cfg),
            "Model": model_cfg,
            "Recording": deepcopy(wfx.recording_cfg),
            "SpeciesPredictor": deepcopy(wfx.species_predictor_cfg),
        }
    }

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    # check member variables
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
            output,
            home / "models",
            "birdnet_default",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(ValueError, match="Output directory does not exist"):
        SparrowWatcher(
            data,
            Path.home() / "iSparrow_output_not_there",
            home / "/models",
            "birdnet_default",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
        )

    with pytest.raises(ValueError, match="Model directory does not exist"):
        SparrowWatcher(
            data,
            output,
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
            data,
            output,
            home / "models",
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
            data,
            output,
            home / "models",
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
            data,
            output,
            home / "models",
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
            delete_recordings="some wrong value",
        )

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg_unrestricted),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    assert watcher.species_presence_model_name == "no species predictor present"
    assert watcher.recording.species_predictor is None

    with pytest.raises(
        ValueError,
        match="'delete_recordings' must be in 'never', 'on_cleanup', 'always'",
    ):
        watcher = SparrowWatcher(
            data,
            output,
            home / "models",
            "birdnet_default",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.model_cfg,
            recording_config=deepcopy(wfx.recording_cfg),
            species_predictor_config=wfx.species_predictor_cfg,
            delete_recordings="immediatelly",
        )


def test_watcher_analysis_lowlevel_functionality(watch_fx, folders, install):
    wfx = watch_fx
    home, data, output = folders

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    # this is normally performed by the `start` method of the watcher,
    # but because this is a low level test of the basic functionality
    # we must do it by hand here:
    watcher.output.mkdir(parents=True, exist_ok=True)
    watcher.may_do_work.set()

    # ... now we can call the functions to be tested

    watcher.analyze(
        home / "example" / "soundscape.wav",
    )

    assert len(list(output.iterdir())) == 1
    datafolder = list(output.iterdir())[0]

    assert len(list(datafolder.iterdir())) == 1
    assert list(datafolder.iterdir()) == [
        Path(datafolder / "results_soundscape.csv"),
    ]

    assert watcher.recording.analyzed is True
    assert watcher.recording.path == home / "example" / "soundscape.wav"
    assert len(watcher.recording.allowed_species) > 0
    assert watcher.recording.species_predictor is not None
    assert len(watcher.recording.analyzer.results) > 0


def test_watcher_daemon_lowlevel_functionality(watch_fx, folders, install):
    wfx = watch_fx
    home, data, output = folders

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

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

    watcher.start()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True
    assert watcher.watcher_process.name == "watcher_process"

    # artificially set finish flag because no data is there
    watcher.is_done_analyzing.set()
    watcher.restart()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True
    assert watcher.watcher_process.name == "watcher_process"

    watcher.is_done_analyzing.set()
    watcher.stop()  # release resources again


def test_watcher_integrated_simple(watch_fx, folders, install):
    wfx = watch_fx

    home, data, output = folders

    for f in data.iterdir():
        if f.is_dir():
            shutil.rmtree(f)
        else:
            f.unlink()

    for f in output.iterdir():
        shutil.rmtree(f)

    assert len(list(Path(data).iterdir())) == 0

    assert len(list(Path(output).iterdir())) == 0

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    path_add = Path(datetime.now().strftime("%y%m%d_%H%M%S"))

    config_should = {
        "Analysis": {
            "input": str(data),
            "output": str(output / path_add),
            "model_dir": str(home / "models"),
            "Preprocessor": deepcopy(wfx.preprocessor_cfg),
            "Model": model_cfg,
            "Recording": deepcopy(wfx.recording_cfg),
            "SpeciesPredictor": deepcopy(wfx.species_predictor_cfg),
        }
    }

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 5
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(
            home,
            data,
            number_of_files,
        ),
    )
    recorder_process.daemon = True

    # run recorder and analyzer process, record start and end times for comparison
    starttime = time.time()

    recorder_process.start()

    watcher.start()

    recorder_process.join()

    endtime = time.time()

    recorder_process.close()

    watcher.stop()

    assert len(list(Path(data).iterdir())) == 5

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    cfgs = [file for file in Path(watcher.output).iterdir() if file.suffix == ".yml"]

    assert len(results) == number_of_files

    assert len(cfgs) == 1

    # load config and check it's consistent

    with open(Path(watcher.output) / "config.yml", "r") as cfgfile:
        cfg = yaml.safe_load(cfgfile)

    assert cfg == config_should

    assert watcher.first_analyzed_file_ct > starttime

    assert watcher.last_analyzed_file_ct < endtime

    assert watcher.last_analyzed_file_ct > watcher.first_analyzed_file_ct


def test_watcher_integrated_delete_always(watch_fx, folders, install):
    wfx = watch_fx

    home, data, output = folders

    for f in data.iterdir():
        if f.is_dir():
            shutil.rmtree(f)
        else:
            f.unlink()

    for f in output.iterdir():
        shutil.rmtree(f)

    assert len(list(Path(data).iterdir())) == 0

    assert len(list(Path(output).iterdir())) == 0

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
        delete_recordings="always",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7
    sleep_for = 2
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(home, data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    recorder_process.start()

    watcher.start()

    while True:
        watcher.pause()
        if (
            watcher.output / "results_example_4.csv"
        ).is_file() and wait_for_file_completion(
            watcher.output / "results_example_4.csv"
        ):
            watcher.stop()
            break
        else:
            watcher.go_on()

    # the following makes
    recorder_process.join()

    recorder_process.close()

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    data = [
        file
        for file in Path(watcher.input_directory).iterdir()
        if file.suffix == ".wav"
    ]
    assert len(data) == 2

    assert len(results) == number_of_files - 2

    watcher.clean_up()

    data = [
        file
        for file in Path(watcher.input_directory).iterdir()
        if file.suffix == ".wav"
    ]

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    assert len(results) == number_of_files

    assert len(data) == 0

    missings = []
    with open(Path(watcher.output) / "missing_files.txt", "r") as mfile:
        for line in mfile:
            if line not in ["\n", "\0"]:
                missings.append(line)

    assert len(missings) == 2


def test_watcher_integrated_delete_on_cleanup(watch_fx, folders, install):
    wfx = watch_fx

    home, data, output = folders

    for f in data.iterdir():
        if f.is_dir():
            shutil.rmtree(f)
        else:
            f.unlink()

    for f in output.iterdir():
        shutil.rmtree(f)

    assert len(list(Path(data).iterdir())) == 0

    assert len(list(Path(output).iterdir())) == 0

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
        delete_recordings="on_cleanup",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7
    sleep_for = 2
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(home, data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    recorder_process.start()

    watcher.start()

    while True:
        watcher.pause()
        if (
            watcher.output / "results_example_4.csv"
        ).is_file() and wait_for_file_completion(
            watcher.output / "results_example_4.csv"
        ):
            watcher.stop()
            break
        else:
            watcher.go_on()

    # the following makes
    recorder_process.join()

    recorder_process.close()

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    data = [
        file
        for file in Path(watcher.input_directory).iterdir()
        if file.suffix == ".wav"
    ]
    assert len(data) == number_of_files

    assert len(results) == number_of_files - 2

    watcher.clean_up()

    data = [
        file
        for file in Path(watcher.input_directory).iterdir()
        if file.suffix == ".wav"
    ]
    assert len(data) == 0

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    assert len(results) == number_of_files

    missings = []
    with open(Path(watcher.output) / "missing_files.txt", "r") as mfile:
        for line in mfile:
            if line not in ["\n", "\0"]:
                missings.append(line.strip("\n"))

    assert missings == [
        str(watcher.input / "example_5.wav"),
        str(watcher.input / "example_6.wav"),
    ]


def test_watcher_integrated_delete_on_never(watch_fx, folders, install):
    wfx = watch_fx

    home, data, output = folders

    for f in data.iterdir():
        if f.is_dir():
            shutil.rmtree(f)
        else:
            f.unlink()

    for f in output.iterdir():
        shutil.rmtree(f)

    assert len(list(Path(data).iterdir())) == 0

    assert len(list(Path(output).iterdir())) == 0

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["model_name"] = "birdnet_default"

    watcher = SparrowWatcher(
        data,
        output,
        home / "models",
        "birdnet_default",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.model_cfg,
        recording_config=deepcopy(wfx.recording_cfg),
        species_predictor_config=wfx.species_predictor_cfg,
        delete_recordings="never",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7
    sleep_for = 2
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(home, data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    recorder_process.start()

    watcher.start()

    while True:
        watcher.pause()
        if (
            watcher.output / "results_example_4.csv"
        ).is_file() and wait_for_file_completion(
            watcher.output / "results_example_4.csv"
        ):
            watcher.stop()
            break
        else:
            watcher.go_on()

    # the following makes
    recorder_process.join()

    recorder_process.close()

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    data = [
        file
        for file in Path(watcher.input_directory).iterdir()
        if file.suffix == ".wav"
    ]
    assert len(data) == number_of_files

    assert len(results) == number_of_files - 2

    watcher.clean_up()

    data = [
        file
        for file in Path(watcher.input_directory).iterdir()
        if file.suffix == ".wav"
    ]
    assert len(data) == 7

    results = [file for file in Path(watcher.output).iterdir() if file.suffix == ".csv"]

    assert len(results) == number_of_files

    missings = []
    with open(Path(watcher.output) / "missing_files.txt", "r") as mfile:
        for line in mfile:
            if line not in ["\n", "\0"]:
                missings.append(line.strip("\n"))

    assert missings == [
        str(watcher.input / "example_5.wav"),
        str(watcher.input / "example_6.wav"),
    ]


