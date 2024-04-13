import pytest
from pathlib import Path
from iSparrow.utils import wait_for_file_completion, read_yaml
from copy import deepcopy
import multiprocessing
import time
from math import isclose


def test_watcher_integrated_simple(watch_fx):
    wfx = watch_fx

    assert len(list(Path(wfx.data).iterdir())) == 0

    assert len(list(Path(wfx.output).iterdir())) == 0

    model_cfg = deepcopy(wfx.model_cfg)

    model_cfg["name"] = "birdnet_default"

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

    assert len(list(Path(wfx.data).iterdir())) == 0

    assert len(list(Path(wfx.output).iterdir())) == 0

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

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    assert len(data) == 2

    assert len(results) == number_of_files - 2

    watcher.clean_up()

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    results = wfx.get_folder_content(watcher.output_directory, ".csv")

    assert len(results) == number_of_files

    assert len(data) == 0

    assert len(wfx.read_missings(watcher)) == 2


def test_watcher_integrated_delete_on_cleanup(watch_fx, folders):
    wfx = watch_fx

    assert len(list(Path(wfx.data).iterdir())) == 0

    assert len(list(Path(wfx.output).iterdir())) == 0

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


def test_watcher_integrated_delete_never(watch_fx, folders):
    wfx = watch_fx

    assert len(list(Path(wfx.data).iterdir())) == 0

    assert len(list(Path(wfx.output).iterdir())) == 0

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

    # the following makes
    recorder_process.join()

    recorder_process.close()

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


def test_watcher_model_exchange_with_cleanup(watch_fx, folders):
    wfx = watch_fx

    assert len(list(Path(wfx.data).iterdir())) == 0

    assert len(list(Path(wfx.output).iterdir())) == 0

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

    while True:
        watcher.pause()

        if (
            watcher.output / "results_example_4.csv"
        ).is_file() and wait_for_file_completion(
            watcher.output / "results_example_4.csv"
        ):
            watcher.change_analyzer(
                "birdnet_custom",
                preprocessor_config=wfx.preprocessor_cfg,
                model_config=wfx.changed_custom_model_cfg,
                recording_config=wfx.changed_custom_recording_cfg,
            )
            # watcher.pause()  # pause again
            watcher.may_do_work.clear()
            break

        else:
            watcher.go_on()

    # make it so that the 5th and 6th audio file are missing from the analysis7
    while True:
        if (watcher.input / "example_7.wav").is_file() and wait_for_file_completion(
            watcher.input / "example_7.wav"
        ):
            watcher.go_on()
            break
        else:
            time.sleep(1)

    # the following makes
    recorder_process.join()

    recorder_process.close()

    watcher.stop()

    assert watcher.model_name == "birdnet_custom"
    assert isclose(watcher.recording_config["min_conf"], 0.35)
    assert isclose(watcher.model_config["sigmoid_sensitivity"], 0.8)
    assert watcher.model_config["default_model_path"] == str(
        wfx.home / "models/birdnet_default"
    )

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    default_results = wfx.get_folder_content(default_output, ".csv")

    custom_results = wfx.get_folder_content(watcher.output, ".csv")

    assert len([folder for folder in watcher.outdir.iterdir() if folder.is_dir()]) == 2

    assert len(data) == 10

    assert len(default_results) == 5

    assert len(custom_results) == 4

    watcher.clean_up()

    custom_results = wfx.get_folder_content(watcher.output, ".csv")

    assert len(custom_results) == 5

    data = wfx.get_folder_content(watcher.input_directory, ".wav")

    assert len(data) == 0

    missings = wfx.read_missings(watcher)

    assert missings == [
        str(watcher.input / "example_5.wav"),
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
