import pytest
from pathlib import Path
from iSparrow.sparrow_watcher import AnalysisEventHandler, SparrowWatcher
from iSparrow.utils import wait_for_file_completion, read_yaml
from iSparrow import SparrowWatcher
from copy import deepcopy
import yaml
from math import isclose
import multiprocessing
import time
from datetime import datetime


def test_watcher_construction(watch_fx):
    wfx = watch_fx
    path_add = Path(datetime.now().strftime("%y%m%d_%H%M"))

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
    assert str(Path(watcher.outdir) / path_add) in str(watcher.output)
    assert str(watcher.input) == str(Path.home() / "iSparrow_tests_data")
    assert str(watcher.outdir) == str(Path.home() / "iSparrow_tests_output")
    assert str(watcher.model_dir) == str(Path.home() / "iSparrow_tests/models")
    assert str(watcher.model_name) == "birdnet_default"
    assert str(Path(watcher.outdir) / path_add) in watcher.output_directory
    assert watcher.input_directory == str(Path.home() / "iSparrow_tests_data")
    assert watcher.is_running is False
    assert watcher.output.is_dir() is False  # not yet created
    assert watcher.outdir.is_dir()
    assert watcher.model_dir.is_dir()
    assert (watcher.model_dir / watcher.model_name).is_dir()
    assert watcher.pattern == ".wav"
    assert watcher.check_time == 1
    assert watcher.delete_recordings == "never"

    path_add = Path(datetime.now().strftime("%y%m%d_%H%M"))
    default_watcher = SparrowWatcher(
        wfx.data,
        wfx.output,
        wfx.home / "models",
        "birdnet_default",
    )

    assert str(Path(default_watcher.outdir) / path_add) in str(default_watcher.output)
    assert str(default_watcher.input) == str(Path.home() / "iSparrow_tests_data")
    assert str(default_watcher.outdir) == str(Path.home() / "iSparrow_tests_output")
    assert str(default_watcher.model_dir) == str(Path.home() / "iSparrow_tests/models")
    assert str(default_watcher.model_name) == "birdnet_default"
    assert (
        str(Path(default_watcher.outdir) / wfx.path_add)
        in default_watcher.output_directory
    )
    assert default_watcher.input_directory == str(Path.home() / "iSparrow_tests_data")
    assert default_watcher.is_running is False
    assert default_watcher.output.is_dir() is False  # not yet created
    assert default_watcher.outdir.is_dir()
    assert default_watcher.model_dir.is_dir()
    assert (default_watcher.model_dir / default_watcher.model_name).is_dir()
    assert default_watcher.pattern == ".wav"
    assert default_watcher.check_time == 1
    assert default_watcher.delete_recordings == "never"

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
            wfx.home / "models",
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
        match="'delete_recordings' must be in 'never', 'always'",
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

    # artificially set the finish flag because we have no data to work with
    watcher.is_done_analyzing.set()
    watcher.stop()
    assert watcher.is_running is False
    assert watcher.watcher_process is None
    assert watcher.may_do_work.is_set() is False
    assert watcher.is_done_analyzing.is_set() is True

    watcher.recording_cfg = wfx.recording_cfg  # necessary because it will be modified
    watcher.start()

    # artificially set finish flag because no data is there
    watcher.recording_cfg = wfx.recording_cfg  # necessary because it will be modified
    watcher.is_done_analyzing.set()
    watcher.restart()
    assert watcher.may_do_work.is_set() is True
    assert watcher.is_running is True
    assert watcher.watcher_process.daemon is True
    watcher.is_done_analyzing.set()
    watcher.stop()


def test_watcher_exceptions(watch_fx, mocker):
    wfx = watch_fx

    watcher = wfx.make_watcher()

    watcher.start()

    with pytest.raises(
        RuntimeError, match="watcher process still running, stop first."
    ):
        watcher.start()

    with pytest.warns(
        UserWarning, match="stop timeout expired, terminating watcher process now."
    ):
        watcher.stop()

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

    mocker.patch(
        "multiprocessing.Process.terminate",
        side_effect=ValueError("Simulated error occurred"),
    )

    watcher.start()

    with pytest.raises(
        RuntimeError,
        match="Something went wrong when trying to stop the watcher process",
    ):
        watcher.stop()

    watcher.watcher_process.kill()
    watcher.watcher_process = None

    mocker.patch(
        "multiprocessing.Process.start",
        side_effect=ValueError("Simulated error occurred"),
    )

    # do something to make the process start and throw
    with pytest.raises(
        RuntimeError,
        match="Something went wrong when starting the watcher process, undoing changes and returning",
    ):
        watcher.start()

    assert watcher.watcher_process is None
    assert watcher.may_do_work.is_set() is False
    assert watcher.is_running is False


def test_watcher_integrated_simple(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher()

    # make a mock recorder process that runs in the background
    number_of_files = 5

    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(
            wfx.home,
            wfx.data,
            number_of_files,
        ),
    )
    recorder_process.daemon = True

    # run recorder and analyzer process, record start and end times for comparison

    recorder_process.start()

    watcher.start()

    recorder_process.join()

    wfx.wait_for_event_then_do(
        condition=lambda: recorder_process.is_alive() is False,
        todo_event=lambda: recorder_process.terminate(),
        todo_else=lambda: time.sleep(0.2),
    )

    recorder_process.close()

    filename = watcher.output / f"results_example_{number_of_files-1}.csv"
    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file(),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: 1,
    )

    assert watcher.is_running is False

    assert watcher.watcher_process is None

    assert len(list(Path(wfx.data).iterdir())) == number_of_files

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    cfgs = wfx.get_folder_content(watcher.output_directory, ".yml")

    assert len(results) == number_of_files

    assert len(cfgs) == 1

    # load config and check it's consistent
    cfg = read_yaml(Path(watcher.output) / "config.yml")

    assert cfg == wfx.config_should


def test_watcher_integrated_delete_always(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="always",
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7

    sleep_for = 10

    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )
    watcher.start()

    wfx.wait_for_event_then_do(
        condition=lambda: watcher.is_running,
        todo_event=lambda: 1,
        todo_else=lambda: time.sleep(0.2),
    )

    recorder_process.daemon = True
    recorder_process.start()

    filename = watcher.output / "results_example_4.csv"

    # stop when the process is done analyzing file 4
    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file(),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: time.sleep(0.2),
    )

    # the following makes
    recorder_process.join()

    recorder_process.close()

    assert watcher.is_running is False
    assert watcher.watcher_process is None

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    assert len(data) > 0
    assert number_of_files > len(results) > 0  # some data is missing


def test_watcher_integrated_delete_never(watch_fx):

    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="never",
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7
    sleep_for = 10
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True

    watcher.start()

    wfx.wait_for_event_then_do(
        condition=lambda: watcher.is_running,
        todo_event=lambda: 1,
        todo_else=lambda: time.sleep(0.2),
    )

    recorder_process.start()

    wfx.wait_for_event_then_do(
        condition=lambda: (watcher.output / "results_example_4.csv").is_file()
        and wait_for_file_completion(watcher.output / "results_example_4.csv"),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: 1,
    )

    recorder_process.join()

    recorder_process.close()

    assert watcher.is_running is False
    assert watcher.watcher_process is None

    wfx.delete_in_output(watcher, ["results_example_6.csv", "results_example_5.csv"])

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert len(data) == number_of_files

    assert len(results) == number_of_files - 2


def test_change_analyzer(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="never",
    )

    old_output = watcher.output

    number_of_files = 15

    sleep_for = 3

    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    watcher.start()

    wfx.wait_for_event_then_do(
        condition=lambda: watcher.is_running,
        todo_event=lambda: 1,
        todo_else=lambda: time.sleep(0.2),
    )

    recorder_process.start()

    filename = watcher.output / "results_example_4.csv"

    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file(),
        todo_event=lambda: watcher.change_analyzer(
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=wfx.changed_custom_recording_cfg,
            delete_recordings="always",
        ),
        todo_else=lambda: time.sleep(0.3),
    )

    # the following makes
    recorder_process.join()

    recorder_process.close()

    assert watcher.model_name == "birdnet_custom"
    assert watcher.output_directory != old_output
    assert (watcher.output / Path("config.yml")).is_file() is True
    assert watcher.preprocessor_config == wfx.custom_preprocessor_cfg
    assert watcher.model_config == wfx.custom_model_cfg
    assert watcher.recording_config == wfx.changed_custom_recording_cfg
    assert watcher.is_running is True
    assert watcher.watcher_process is not None
    assert watcher.input_directory == str(Path.home() / "iSparrow_tests_data")
    assert watcher.output.is_dir() is True  # not yet created
    assert (watcher.model_dir / watcher.model_name).is_dir()
    assert watcher.pattern == ".wav"
    assert watcher.check_time == 1
    assert watcher.delete_recordings == "always"
    # wait for the final file to be completed
    filename = watcher.output / f"results_example_{number_of_files-1}.csv"

    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file(),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: time.sleep(0.3),
    )

    current_files = [f for f in watcher.output.iterdir() if f.suffix == ".csv"]
    old_files = [f for f in old_output.iterdir() if f.suffix == ".csv"]

    assert len(current_files) > 0  # some analyzed files must be in the new directory
    assert len(old_files) > 0
    assert 0 < len(list(Path(wfx.data).iterdir())) < number_of_files
    assert number_of_files >= len(old_files) + len(current_files)  # some data can be


def test_change_analyzer_recovery(watch_fx, mocker):

    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="never",
    )

    old_output = watcher.output

    number_of_files = 15

    sleep_for = 6

    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )

    recorder_process.daemon = True

    watcher.start()

    wfx.wait_for_event_then_do(
        condition=lambda: watcher.is_running,
        todo_event=lambda: 1,
        todo_else=lambda: time.sleep(0.5),
    )

    recorder_process.start()

    assert watcher.is_running
    assert watcher.watcher_process is not None

    filename = watcher.output / "results_example_4.csv"

    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file(),
        todo_event=lambda: 1,
        todo_else=lambda: time.sleep(0.3),
    )

    # patch the start method so we get a mock exception that is propagated through the system
    mocker.patch(
        "iSparrow.SparrowWatcher.restart",
        side_effect=ValueError("Simulated error occurred"),
    )
    try:
        watcher.change_analyzer(
            "birdnet_custom",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=wfx.changed_custom_recording_cfg,
            delete_recordings="always",
        )
    except RuntimeError as e:
        e == RuntimeError(
            "Error when restarting the watcher process, any changes made have been undone. The process needs to be restarted manually. This operation may have led to data loss."
        )
        watcher.start()

    assert watcher.is_running
    assert watcher.model_name == "birdnet_default"
    assert watcher.delete_recordings == "never"

    filename = watcher.output / f"results_example_{number_of_files -1}.csv"
    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file() and wait_for_file_completion(filename),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: time.sleep(1),
    )

    results_folders = [f for f in watcher.outdir.iterdir() if f.is_dir()]
    results = [f for f in watcher.output.iterdir() if f.suffix == ".csv"]
    old_results = [f for f in old_output.iterdir() if f.suffix == ".csv"]

    assert old_output != watcher.output
    assert len(results_folders) == 2
    assert len(old_results) == 5
    assert len(results) <= number_of_files - 1

    old_cfg = read_yaml(old_output / "config.yml")
    new_cfg = read_yaml(watcher.output / "config.yml")
    assert old_cfg["Analysis"]["Model"] == new_cfg["Analysis"]["Model"]
    assert old_cfg["Analysis"]["Preprocessor"] == new_cfg["Analysis"]["Preprocessor"]
    assert old_cfg["Analysis"]["Recording"] == new_cfg["Analysis"]["Recording"]


def test_change_analyzer_exception(watch_fx, mocker):
    # patch the start method so we get a mock exception that is propagated through the system
    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="never",
    )

    old_recording_cfg = deepcopy(watcher.recording_config)
    old_model_cfg = deepcopy(watcher.model_config)
    old_preprocessor_cfg = deepcopy(watcher.preprocessor_config)
    old_species_predictor_cfg = deepcopy(watcher.species_predictor_config)

    number_of_files = 20

    sleep_for = 3

    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )

    recorder_process.daemon = True

    watcher.start()

    wfx.wait_for_event_then_do(
        condition=lambda: watcher.is_running,
        todo_event=lambda: 1,
        todo_else=lambda: time.sleep(0.25),
    )

    recorder_process.start()

    assert watcher.is_running
    assert watcher.watcher_process is not None

    filename = watcher.output / f"results_example_{4}.csv"
    wfx.wait_for_event_then_do(
        condition=lambda: filename.is_file(),
        todo_event=lambda: 1,  # do nothing, just stop waiting,
        todo_else=lambda: time.sleep(0.2),
    )

    old_output = watcher.output_directory

    with pytest.raises(
        ValueError, match="Given model name does not exist in model dir."
    ):
        watcher.change_analyzer(
            "nonexistent_model",
            preprocessor_config=wfx.custom_preprocessor_cfg,
            model_config=wfx.custom_model_cfg,
            recording_config=wfx.changed_custom_recording_cfg,
            delete_recordings="always",
        )
    assert watcher.model_name == "birdnet_default"
    assert watcher.is_running
    assert watcher.output_directory == old_output
    assert watcher.model_config == old_model_cfg
    assert watcher.preprocessor_config == old_preprocessor_cfg
    assert watcher.recording_config == old_recording_cfg
    assert watcher.species_predictor_config == old_species_predictor_cfg

    watcher.stop()
