from iSparrow import SparrowRecording
from iSparrow import SpeciesPredictorBase
import iSparrow.utils as utils

from pathlib import Path
import threading
import pandas as pd
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from time import sleep
from datetime import datetime
from copy import deepcopy
import yaml
import multiprocessing


class AnalysisEventHandler(FileSystemEventHandler):
    """
    AnalysisEventHandler Custom event handler that calls a function whenever
    the a new file with a matching extension is created in the watched directory and that waits for a
    multiprocessing.Event object to be true.

    Base:
        FileSystemEventHandler: watchdog.FilesystemEventHandler

    Methods:
    --------
    on_created(event): Run the callback whenever a newly created file with a matching pattern is found.
    """

    def __init__(
        self,
        callback: callable,
        wait_event: multiprocessing.Event,
        pattern: str = ".wav",
    ):
        """
        __init__ Create a new AnalysisEventHandler object.

        Args:
            callback (callable): Callback functionw hen
            wait_event (multiprocessing.Event): _description_
            pattern (str, optional): _description_. Defaults to ".wav".
        """
        self.wait_event = wait_event
        self.callback = callback
        self.pattern = pattern
        self.finish_event = threading.Event()

    def on_created(self, event):
        """
        on_created Call the callback function of the caller object whenever a new file is created
                    that has the desired file extension. Waits on the stored multiprocessing.event and only
                    runs if its flag is true.

        Args:
            event (multiprocessing.Event): _description_
        """
        if (
            Path(event.src_path).is_file()
            and Path(event.src_path).suffix == self.pattern
        ):
            self.wait_event.wait()
            self.callback(event.src_path)
            self.finish_event.set()


def watchertask(watcher):
    """
    watchertask Function to run in the watcher process.
    Checks if there is a new file every 'watcher.check_time' minutes and
    analyze the file with a sound classifier model.

    Args:
        watcher (SparrowWatcher): Watcher class to run this task with

    Raises:
        RuntimeError: When something goes wrong inside the analyzer process.
    """
    observer = Observer()
    event_handler = AnalysisEventHandler(
        watcher.analyze,
        watcher.wait_event,
        pattern=watcher.pattern,
    )
    observer.schedule(event_handler, watcher.input, recursive=True)
    observer.start()

    try:
        while True:
            sleep(watcher.check_time)
    except SystemExit:
        print("waiting to finish")
        event_handler.finish_event.wait()  # wait for current task to finish
        observer.stop()
    except KeyboardInterrupt:
        print("waiting to finish")
        event_handler.finish_event.wait()  # wait for current task to finish
        observer.stop()
    except Exception as e:
        observer.stop()
        raise RuntimeError(
            "Something went wrong in the watcher/analysis process"
        ) from e

    observer.join()


class SparrowWatcher:
    """
    Class that watches a directory and applies a classifier model to each new file that is created in it.
    Supports model exchange on the fly.
    To this end, it creates a daemon thread in which the classifier runs,
    such that commands can be processed in the main process.

    Methods:
    --------
    change_analyzer: Exchange the classifier model with one that is present in the model dir.
    analyze: Analyze a file and write the results to the output directory.
    save_results: Save the results to the output directory as a csv file.
    stop: Pause the watcher thread.
    go_on: Continue the watcher thread
    check_analysis: Go over the input and output directory and repeat analysis for
                    all files for which there is not corresponding file in the output
                    directory.

    """

    def _write_config(self):
        """
        _write_config Write the parameters used to configure the caller to file.
        """
        with open(self.output / "config.yml", "w") as ymlfile:
            yaml.safe_dump(self.config, ymlfile)

    def _set_up_recording(
        self,
        model_name: str,
        preprocessor_config: dict = {},
        model_config: dict = {},
        recording_config: dict = {},
        species_predictor_config: dict = {},
    ):
        """
        _set_up_recording _summary_

        _extended_summary_

        Args:
            model_name (str): _description_
            preprocessor_config (dict, optional): _description_. Defaults to {}.
            model_config (dict, optional): _description_. Defaults to {}.
            recording_config (dict, optional): _description_. Defaults to {}.
            species_predictor_config (dict, optional): _description_. Defaults to {}.

        Raises:
            ValueError: _description_
        """
        preprocessor = utils.load_name_from_module(
            "pp",
            self.model_dir / Path(model_name) / "preprocessor.py",
            "Preprocessor",
        )(**preprocessor_config)

        model = utils.load_name_from_module(
            "mo", self.model_dir / Path(model_name) / "model.py", "Model"
        )(model_path=self.model_dir / model_name, **model_config)

        # process config file
        self.config = {
            "Analysis": {
                "input": str(self.input),
                "output": str(self.output),
                "model_dir": str(self.model_dir),
                "Preprocessor": deepcopy(preprocessor_config),
                "Model": deepcopy(model_config),
                "Recording": deepcopy(recording_config),
                "SpeciesPredictor": deepcopy(species_predictor_config),
            }
        }

        self.config["Analysis"]["Model"]["model_name"] = model_name

        self._write_config()

        self.species_predictor = None

        # process species range predictor
        if all(name in recording_config for name in ["date", "lat", "lon"]) and all(
            recording_config[name] is not None for name in ["date", "lat", "lon"]
        ):

            try:
                # we can use the species predictor
                species_predictor = SpeciesPredictorBase(
                    model_path=self.model_dir / model_name,
                    **species_predictor_config,
                )

                recording_config["species_predictor"] = species_predictor

            except Exception as e:
                raise ValueError(
                    "An error occured during species range predictor creation. Does you model provide a model file called 'species_presence_model'?"
                ) from e

        # create recording object
        # species predictor is applied here once and then used for all the analysis calls that may follow
        self.recording = SparrowRecording(preprocessor, model, "", **recording_config)

    def __init__(
        self,
        indir: str,
        outdir: str,
        model_dir: str,
        model_name: str,
        preprocessor_config: dict = {},
        model_config: dict = {},
        recording_config: dict = {},
        species_predictor_config: dict = {},
        pattern: str = ".wav",
        check_time: int = 1,
        delete_recordings: str = "on_cleanup",
    ):
        """
        __init__ Create a new Watcher object.

        Args:
            indir (str): Directory to read files from
            outdir (str): Directory to write the analysis results to.
                        A new directory with a timestamp for name will be
                        created within it to store the result files in.
            model_dir (str): Directory where downloaded models are stored
            model_name (str): name of the model to use. Must match the directory name it is stored in, e.g., 'birdnet_default'.
            preprocessor_config (dict, optional): Keyword arguments for the preprocessor of the model. Defaults to {}.
            model_config (dict, optional): Keyword arguments for the model instance. Defaults to {}.
            recording_config (dict, optional): Keyword arguments for the internal SparrowRecording. Defaults to {}.
            species_predictor_config (dict, optional): Keyword arguments for a species presence predictor model. Defaults to {}.
            check_time(int, optional): Sleep time of the thread between checks for new files in seconds. Defaults to 1.
            delete_recordings(str, optional): Mode for data clean up. Can be one of "never", "on_cleanup", "immediatelly". "never" keeps recordings around indefinitely, "on_cleanup" only deletes them when the `clean_up` method is called, and 'immediatelly' deletes the recording immediatelly after analysis.
        Raises:
            ValueError: When the indir parameter is not an existing directory.
            ValueError: When the outdir parameter is not an existing directory.
            ValueError: When the model_dir parameter is not an existing directory.
            ValueError: When the model name does not correspond to a directory in the 'model_dir' directory in which available models are stored.
            Exception: When the species presence model should be used: If something goes wrong during creation of the species presence predictor model.
        """
        # set up data to use
        self.input = Path(indir)

        if self.input.is_dir() is False:
            raise ValueError("Input directory does not exist")

        self.outdir = outdir

        if self.outdir.is_dir() is False:
            raise ValueError("Output directory does not exist")

        self.output = Path(self.outdir) / Path(datetime.now().strftime("%y%m%d_%H%M%S"))

        self.output.mkdir(exist_ok=True, parents=True)

        self.model_dir = Path(model_dir)

        if self.model_dir.is_dir() is False:
            raise ValueError("Model directory does not exist")

        if (self.model_dir / model_name).is_dir() is False:
            raise ValueError("Given model name does not exist in model directory")

        self.pattern = pattern

        self.model = None

        self.preprocessor = None

        self.watcher_process = None

        self.wait_event = None

        self.check_time = check_time

        if delete_recordings not in ["never", "on_cleanup", "always"]:
            raise ValueError(
                "'delete_recordings' must be in 'never', 'on_cleanup', 'always'"
            )

        self.delete_recordings = delete_recordings

        self._set_up_recording(
            model_name,
            preprocessor_config=preprocessor_config,
            model_config=model_config,
            recording_config=recording_config,
            species_predictor_config=species_predictor_config,
        )

        self.results = []

    @property
    def output_directory(self):
        return str(self.output)

    @property
    def input_directory(self):
        return str(self.input)

    @property
    def is_active(self):
        if self.watcher_process is not None:
            return self.watcher_process.is_alive()
        else:
            return False

    @property
    def model_name(self):
        return self.recording.analyzer.name

    @property
    def preprocessor_name(self):
        return self.recording.processor.name

    @property
    def species_presence_model_name(self):
        if self.recording.species_predictor:
            return self.recording.species_predictor.name
        else:
            return "no species predictor present"

    def change_analyzer(
        self,
        model_name: str,
        preprocessor_config: dict = {},
        model_config: dict = {},
        recording_config: dict = {},
        species_predictor_config: dict = {},
    ):
        """
        change_analyzer _summary_

        Args:
            model_name (str): _description_
            preprocessor_config (dict, optional): _description_. Defaults to {}.
            model_config (dict, optional): _description_. Defaults to {}.
            recording_config (dict, optional): _description_. Defaults to {}.
            species_predictor_config (dict, optional): _description_. Defaults to {}.

        Raises:
            ValueError: _description_
        """
        # import and build new model, pause the analyzer process,
        # change the model, resume the analyzer

        if (self.model_dir / model_name).is_dir() is False:
            raise ValueError("Given model name does not exist in model dir.")

        self._set_up_recording(
            model_name,
            preprocessor_config,
            model_config=model_config,
            recording_config=recording_config,
            species_predictor_config=species_predictor_config,
        )

        # restart process to make changes take effect
        self.restart()

    def analyze(self, filename: str):
        """
        analyze Analyze a file pointed to by 'filename' and save the results as csv file to 'output'.

        Args:
            filename (str): path to the file to analyze.
        """
        self.recording.path = filename

        self.recording.analyzed = False  # reactivate

        self.recording.analyze()

        results = self.recording.detections

        self.save_results(results, suffix=Path(filename).stem)

        if self.delete_recordings == "immediatelly":
            Path(filename).unlink()

    def save_results(self, results: list, suffix=""):
        """
        save_results Save results to csv file.

        Args:
            suffix (str, optional): _description_. Defaults to "".
        """
        pd.DataFrame(results).to_csv(self.output / Path(f"results_{suffix}.csv"))

    def start(self):
        """
        watch Watch the directory the caller has been created with and analyze all newly created files matching a certain file ending. \
            Creates a new daemon process in which the analysis function runs.
        """
        if self.watcher_process is not None and self.is_active():
            raise RuntimeError("watcher process still running, stop first.")

        print("start the watcher process")
        # create a background watchertask such that the command is handed back to the parent process
        self.wait_event = (
            multiprocessing.Event()
        )  # README: event currently only there for a multiprocessing template

        self.wait_event.set()
        self.watcher_process = multiprocessing.Process(target=watchertask, args=(self,))
        self.watcher_process.daemon = True
        self.watcher_process.start()

    def restart(self):
        """
        restart Restart the watcher process. Must be called when, e.g., new models have been loaded or the input or output has changed.
        """
        self.stop()
        self.start()

    def pause(self):
        """
        stop Pause the watcher thread.
        """
        if self.watcher_process.is_alive():
            print("pause the watcher process")
            self.wait_event.clear()
        else:
            raise RuntimeError("Cannot pause watcher process, is not alive anymore.")

    def go_on(self):
        """
        go_on Continue the watcher thread.
        """
        if self.watcher_process.is_alive():
            print("continute the watcher process")
            self.wait_event.set()
        else:
            raise RuntimeError("Cannot continue watcher process, is not alive anymore.")

    def stop(self):
        if self.watcher_process.is_alive():
            print("stop the watcher process")
            self.watcher_process.terminate()
            self.watcher_process.join()
        else:
            raise RuntimeError("Cannot stop watcher process, is not alive anymore.")

    def clean_up(self):
        """
        clean_up Delete the input files which have been analyzed and delete them if 'delete' is True.
                Files that have not yet been analyzed are analyzed before deletion.

        Args:
        """
        missings = []
        for filename in self.input.iterdir():
            if (
                self.output / Path(f"results_{str(filename.stem)}.csv")
            ).exists() is False:
                self.analyze(filename)
                missings.append(filename)

            if self.delete_recordings == "on_cleanup":
                filename.unlink()

            with open(self.output / "missing_files.csv", "w") as missingrecord:
                for line in missings:
                    missingrecord.write(f"{line}\n")
