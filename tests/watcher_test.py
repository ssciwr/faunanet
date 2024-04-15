import pytest
from pathlib import Path
from iSparrow.sparrow_watcher import AnalysisEventHandler
from iSparrow.utils import wait_for_file_completion, read_yaml
from iSparrow import SparrowWatcher
from copy import deepcopy
import yaml
from math import isclose
import multiprocessing
import time


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
    starttime = time.time()

    recorder_process.start()

    watcher.start()

    recorder_process.join()

    endtime = time.time()

    while True:
        if recorder_process.is_alive() is False:
            break
        else:
            time.sleep(1)

    recorder_process.close()

    watcher.stop()

    assert len(list(Path(wfx.data).iterdir())) == 5

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    cfgs = wfx.get_folder_content(watcher.output_directory, ".yml")

    assert len(results) == number_of_files

    assert len(cfgs) == 1

    # load config and check it's consistent
    cfg = read_yaml(Path(watcher.output) / "config.yml")

    assert cfg == wfx.config_should

    assert watcher.first_analyzed_file_ct > starttime

    assert watcher.last_analyzed_file_ct < endtime

    assert watcher.last_analyzed_file_ct > watcher.first_analyzed_file_ct


def test_watcher_integrated_delete_always(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="always",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7

    sleep_for = 2

    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    recorder_process.start()

    watcher.start()

    file = watcher.output / "results_example_4.csv"

    # pause when the process is done analyzing file 4
    wfx.wait_for_event_then_do(
        condition=lambda: file.is_file() and wait_for_file_completion(file),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: time.sleep(1),
    )

    # the following makes
    recorder_process.join()

    recorder_process.close()
    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    present_indices = [
        0,
        1,
        2,
        3,
        4,
        5,
    ]

    assert data == [
        watcher.input / "example_6.wav",
    ]

    assert results == [
        watcher.output / f"results_example_{i}.csv" for i in present_indices
    ]

    watcher.clean_up()

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert results == [
        watcher.output / f"results_example_{i}.csv"
        for i in range(0, number_of_files, 1)
    ]

    assert len(data) == 0

    missings = wfx.read_missings(watcher)

    assert missings == [
        watcher.input / "example_6.wav",
    ]


def test_watcher_integrated_delete_on_cleanup(watch_fx):

    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="on_cleanup",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7
    sleep_for = 2
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    recorder_process.start()

    watcher.start()

    file = watcher.output / "results_example_4.csv"

    wfx.wait_for_event_then_do(
        condition=lambda: file.is_file() and wait_for_file_completion(file),
        todo_event=lambda: watcher.stop(),
        todo_else=lambda: 1,
    )
    # the following makes
    recorder_process.join()

    recorder_process.close()

    wfx.delete_in_output(watcher, ["results_example_6.csv", "results_example_5.csv"])

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert len(data) == number_of_files

    assert len(results) == number_of_files - 2

    watcher.clean_up()

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    assert len(data) == 0

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert len(results) == number_of_files

    missings = wfx.read_missings(watcher)

    missings.sort()

    assert missings == [
        str(watcher.input / "example_5.wav"),
        str(watcher.input / "example_6.wav"),
    ]


def test_watcher_integrated_delete_never(watch_fx):

    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="never",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 7
    sleep_for = 2
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
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

    recorder_process.join()

    recorder_process.close()

    wfx.delete_in_output(watcher, ["results_example_6.csv", "results_example_5.csv"])

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert len(data) == number_of_files

    assert len(results) == number_of_files - 2

    watcher.clean_up()

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    assert len(data) == 7

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert len(results) == number_of_files

    missings = wfx.read_missings(watcher)

    assert missings == [
        str(watcher.input / "example_5.wav"),
        str(watcher.input / "example_6.wav"),
    ]


def test_watcher_model_exchange_with_cleanup(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="on_cleanup",
        reanalyze_on_cleanup=True,
    )

    # make a mock recorder process that runs in the background
    number_of_files = 10
    sleep_for = 6
    recorder_process = multiprocessing.Process(
        target=wfx.mock_recorder,
        args=(wfx.home, wfx.data, number_of_files, sleep_for),
    )
    recorder_process.daemon = True
    recorder_process.start()

    watcher.start()

    default_output = deepcopy(watcher.output)

    # wait until the 4th file has been analyzed
    filename = watcher.output / "results_example_4.csv"
    wfx.wait_for_event_then_do(
        lambda: filename.is_file() and wait_for_file_completion(filename),
        lambda: 1,
        lambda: time.sleep(1),
    )

    watcher.change_analyzer(
        "birdnet_custom",
        preprocessor_config=wfx.preprocessor_cfg,
        model_config=wfx.changed_custom_model_cfg,
        recording_config=wfx.changed_custom_recording_cfg,
    )

    #  kill mock recorder process
    recorder_process.join()

    recorder_process.close()

    # wait until the stuff is done
    filename = watcher.output / f"results_example_{number_of_files - 1}.csv"
    wfx.wait_for_event_then_do(
        lambda: filename.is_file() and wait_for_file_completion(filename),
        lambda: watcher.stop(),
        lambda: 1,
    )

    assert len(watcher.used_output_folders) == 2
    assert watcher.model_name == "birdnet_custom"
    assert isclose(watcher.recording_config["min_conf"], 0.35)
    assert isclose(watcher.model_config["sigmoid_sensitivity"], 0.8)
    assert watcher.model_config["default_model_path"] == str(
        wfx.home / "models/birdnet_default"
    )

    # delete example files to simulate missing ones. because the temporal succession of
    # file writing and model xchange is not completely reliable, we need to check file
    # existence
    wfx.delete_in_output(watcher, ["results_example_6.csv", "results_example_5.csv"])

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    default_results = wfx.get_folder_content(default_output, ".csv")

    custom_results = wfx.get_folder_content(watcher.output, ".csv")

    assert len([folder for folder in watcher.outdir.iterdir() if folder.is_dir()]) == 2

    assert len(data) == 10

    assert len(default_results) == 5

    assert len(custom_results) == 3

    watcher.clean_up()

    custom_results = wfx.get_folder_content(watcher.output, ".csv")

    assert len(custom_results) == 5

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    assert len(data) == 0

    missings = wfx.read_missings(watcher)

    assert missings == [
        str(watcher.input / "example_5.wav"),
        str(watcher.input / "example_6.wav"),
    ]


def test_watcher_model_exchange_with_cleanup_invalid_model(watch_fx):
    wfx = watch_fx

    watcher = wfx.make_watcher(
        delete_recordings="on_cleanup",
        reanalyze_on_cleanup=True,
    )

    watcher.start()

    time.sleep(4)

    # artificially set finish flag because no data
    watcher.is_done_analyzing.set()

    with pytest.raises(
        ValueError, match="Given model name does not exist in model dir."
    ):
        watcher.change_analyzer(
            "model_that_is_not_there",
            preprocessor_config=wfx.preprocessor_cfg,
            model_config=wfx.changed_custom_model_cfg,
            recording_config=wfx.changed_custom_recording_cfg,
        )

    assert watcher.watcher_process is None
    assert watcher.is_running is False
