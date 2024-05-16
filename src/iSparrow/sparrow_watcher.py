from iSparrow import SparrowRecording
from iSparrow import SpeciesPredictorBase
import iSparrow.utils as utils

from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from time import sleep
from datetime import datetime
from copy import deepcopy
import yaml
import multiprocessing
import warnings
import csv
import sys
from contextlib import contextmanager


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
        watcher,
    ):
        """
        __init__ Create a new AnalysisEventHandler object.

        Args:
            callback (callable): Callback functionw hen
            pattern (str, optional): file apttern. Defaults to ".wav".
            watcher: (SparrowWatcher): Watcher this Handler is used with
        """
        self.pattern = watcher.pattern
        self.recording = watcher._set_up_recording(
            watcher.model_name,
            watcher.recording_config,
            watcher.species_predictor_config,
            watcher.model_config,
            watcher.preprocessor_config,
        )
        self.callback = watcher.analyze

    def on_created(self, event):
        """
        on_created Call the callback function of the caller object whenever a new file is created
                    that has the desired file extension. Waits on the stored multiprocessing.event and only
                    runs if its flag is true.

        Args:
            event (threading.Event): Event triggering the analysis, i.e., a new audio file appears and is ready to be processessed in the watched folder
        """
        if (
            Path(event.src_path).is_file()
            and Path(event.src_path).suffix == self.pattern
        ):
            self.callback(event.src_path, self.recording)


def watchertask(watcher):
    """
    watchertask Function to run in the watcher process.
    Checks if there is a new file every 'watcher.check_time' seconds and
    analyze the file with a sound classifier model.

    Args:
        watcher (SparrowWatcher): Watcher class to run this task with

    Raises:
        RuntimeError: When something goes wrong inside the analyzer process.
    """
    # sys.stdout = open(watcher.output / "stdout.txt", "w")
    # sys.stderr = open(watcher.output / "stderr.txt", "w")

    try:
        # build the recorder
        observer = Observer()

        event_handler = AnalysisEventHandler(
            watcher,
        )
        observer.schedule(event_handler, watcher.input, recursive=True)
        observer.start()

        try:
            while True:
                sleep(watcher.check_time)
        except KeyboardInterrupt:
            observer.stop()
        except Exception as e:
            observer.stop()
            raise RuntimeError(
                "Something went wrong in the watcher/analysis process"
            ) from e

        observer.join()
    finally:
        pass
        # sys.stdout.close()
        # sys.stderr.close()


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

    def _write_config(
        self,
    ):
        """
        _write_config Write out the set of parameters a Watcher instance has been created with.

        """
        config = {
            "Analysis": {
                "input": str(self.input),
                "output": str(self.output),
                "delete_recordings": self.delete_recordings,
                "pattern": self.pattern,
                "model_name": self.model_name,
                "check_time": self.check_time,
                "model_dir": str(self.model_dir),
                "Preprocessor": deepcopy(self.preprocessor_config),
                "Model": deepcopy(self.model_config),
                "Recording": deepcopy(self.recording_config),
                "SpeciesPredictor": deepcopy(self.species_predictor_config),
            }
        }

        try:
            with open(self.output / "config.yml", "w") as ymlfile:
                yaml.safe_dump(config, ymlfile)
        except Exception as e:
            raise RuntimeError("Error during config writing ", e) from e

    def _set_up_recording(
        self,
        model_name: str,
        recording_config: dict,
        species_predictor_config: dict,
        model_config: dict,
        preprocessor_config: dict,
    ) -> SparrowRecording:
        """
        _set_up_recording Build a new recording from configs

        Args:
            model_name (str): name of the model to use
            recording_config (dict): recording config
            species_predictor_config (dict): species_predictor config
            model_config (dict): model config data
            preprocessor_config (dict): preprocessor config data

        Raises:
            ValueError: In case the species presence predictor is used. When the an error occurs during the creation of the species predictor model.

        Returns:
            SparrowRecording: New instance of SpeciesRecording created with config dictionaries held by the caller.
        """
        recording_config = deepcopy(recording_config)

        preprocessor = utils.load_name_from_module(
            "pp",
            self.model_dir / Path(model_name) / "preprocessor.py",
            "Preprocessor",
        )(**preprocessor_config)

        model = utils.load_name_from_module(
            "mo", self.model_dir / Path(model_name) / "model.py", "Model"
        )(model_path=self.model_dir / model_name, **model_config)

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

        # make sure the date is set correctly
        if "date" in self.recording_config:
            if self.recording_config["date"] == "today":
                self.recording_config["date"] = datetime.now()
            elif isinstance(self.recording_config["date"], str):
                self.recording_config["date"] = datetime.strptime(
                    self.recording_config["date"], "%d/%m/%Y"
                )
            else:
                pass
        # create recording object
        # species predictor is applied here once and then used for all the analysis calls that may follow
        return SparrowRecording(preprocessor, model, "", **recording_config)

    def _restore_old_state(self, old_state: dict):
        """
        _restore_old_state Restore state of the watcher instance to the state it had before a change was made.

        Args:
            old_state (dict):  Dictionary containing the old state of the calling object
        """
        self.model_name = old_state["model_name"]
        self.preprocessor_config = old_state["preprocessor_config"]
        self.model_config = old_state["model_config"]
        self.recording_config = old_state["recording_config"]
        self.species_predictor_config = old_state["species_predictor_config"]
        self.pattern = old_state["pattern"]
        self.check_time = old_state["check_time"]
        self.delete_recordings = old_state["delete_recordings"]

    @contextmanager
    def _backup_and_restore_state(self) -> dict:
        """
        _backup_and_restore_state Helper context manager that creates a backup of the current object state and restores it in case of an error.

        Raises:
            RuntimeError When an error occurs during the restart of the watcher process.

        Yields:
            dict: Dictionary containing the old state of the calling object
        """
        old_state = {
            "model_name": deepcopy(self.model_name),
            "preprocessor_config": deepcopy(self.preprocessor_config),
            "model_config": deepcopy(self.model_config),
            "recording_config": deepcopy(self.recording_config),
            "species_predictor_config": deepcopy(self.species_predictor_config),
            "pattern": deepcopy(self.pattern),
            "check_time": self.check_time,
            "delete_recordings": self.delete_recordings,
        }

        try:
            yield old_state
        except Exception as e:
            self._restore_old_state(old_state)

            if self.is_running:
                self.stop()

            raise RuntimeError(
                "Error when while trying to change the watcher process, any changes made have been undone. The process needs to be restarted manually. This operation may have led to data loss."
            ) from e

    def __init__(
        self,
        indir: str,
        outdir: str,
        model_dir: str,
        model_name: str,
        preprocessor_config: dict = None,
        model_config: dict = None,
        recording_config: dict = None,
        species_predictor_config: dict = None,
        pattern: str = ".wav",
        check_time: int = 1,
        delete_recordings: str = "never",
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
            pattern (str, optional): filename pattern to look for. defaults to '.wav'.
            check_time(int, optional): Sleep time of the watcher between checks for new files in seconds. Defaults to 1.
            delete_recordings(str, optional): Mode for data clean up. Can be one of "never" or "always".
                                            "never" keeps recordings around indefinitely. 'always' deletes the recording
                                            immediatelly after analysis. Defaults to 'never'.
        Raises:
            ValueError: When the indir parameter is not an existing directory.
            ValueError: When the outdir parameter is not an existing directory.
            ValueError: When the model_dir parameter is not an existing directory.
            ValueError: When the model name does not correspond to a directory in the 'model_dir' directory in which available models are stored.
        """
        if preprocessor_config is None:
            preprocessor_config = {}

        if model_config is None:
            model_config = {}

        if recording_config is None:
            recording_config = {}

        if species_predictor_config is None:
            species_predictor_config = {}

        # set up data to use
        self.input = Path(indir)

        if self.input.is_dir() is False:
            raise ValueError("Input directory does not exist")

        self.outdir = Path(outdir)

        if self.outdir.is_dir() is False:
            raise ValueError("Output directory does not exist")

        self.output = None
        self.old_output = None

        self.model_dir = Path(model_dir)

        if self.model_dir.is_dir() is False:
            raise ValueError("Model directory does not exist")

        if (self.model_dir / model_name).is_dir() is False:
            raise ValueError("Given model name does not exist in model directory")

        self.pattern = pattern

        self.model_name = model_name

        self.watcher_process = None

        self.may_do_work = multiprocessing.Event()

        self.is_done_analyzing = multiprocessing.Event()

        self.check_time = check_time

        if delete_recordings not in ["never", "always"]:
            raise ValueError("'delete_recordings' must be in 'never', 'always'")

        self.delete_recordings = delete_recordings

        self.first_analyzed = multiprocessing.Value("i", 0)

        self.last_analyzed = multiprocessing.Value("i", 0)

        self.preprocessor_config = deepcopy(preprocessor_config)

        self.model_config = deepcopy(model_config)

        self.recording_config = deepcopy(recording_config)

        self.species_predictor_config = deepcopy(species_predictor_config)

        self.batchfile_name = "batch_info.yml"


    @property
    def output_directory(self):
        return str(self.output)

    @property
    def input_directory(self):
        return str(self.input)

    @property
    def is_running(self):
        if self.watcher_process is not None:
            return self.watcher_process.is_alive()
        else:
            return False

    @property
    def is_sleeping(self):
        if self.watcher_process is not None:
            return self.may_do_work.is_set() is False
        else:
            return False

    def analyze(self, filename: str, recording: SparrowRecording):
        """
        analyze Analyze a file pointed to by 'filename' and save the results as csv file to 'output'.

        Args:
            filename (str): path to the file to analyze.
            recording (SparrowRecording): recording object to use
        """
        self.may_do_work.wait()  # wait until parent process allows the worker to pick up work

        recording.path = filename

        recording.analyzed = False  # reactivate

        # make the main process wait on the finish signal to make sure no
        # corrupt files are produced
        self.is_done_analyzing.clear()

        self.last_analyzed.value = int(Path(filename).stat().st_ctime)

        if self.first_analyzed.value == 0:
            self.first_analyzed.value = self.last_analyzed.value

        recording.analyze()

        results = recording.detections

        self.save_results(self.output, results, suffix=Path(filename).stem)

        self.is_done_analyzing.set()  # give good-to-go for main process

        if self.delete_recordings == "always":
            Path(filename).unlink()

    def save_results(self, outfolder: str, results: list, suffix=""):
        """
        save_results Save results to csv file.

        Args:
            outfolder (str): folder to save the results in
            suffix (str, optional): _description_. Defaults to "".
        """

        with open(Path(outfolder) / Path(f"results_{suffix}.csv"), "w") as csvfile:
            if len(results) == 0:
                writer = csv.writer(csvfile)
                writer.writerow([])
            else:
                colnames = results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=colnames)
                writer.writeheader()
                writer.writerows(results)

    def start(self):
        """
        start Watch the directory the caller has been created with and analyze all newly created files matching a certain file ending. \
            Creates a new daemon process in which the analysis function runs.

        Raises:
            RuntimeError: When the watcher process is running already.
        """
        if self.is_running:
            raise RuntimeError("watcher process still running, stop first.")

        self.old_output = self.output
        self.output = Path(self.outdir) / Path(datetime.now().strftime("%y%m%d_%H%M%S"))
        self.output.mkdir(exist_ok=True, parents=True)
        self.first_analyzed.value = 0
        self.last_analyzed.value = 0

        self._write_config()

        try:
            print("start the watcher process")
            # create a background watchertask such that the command is handed back to the parent process
            self.watcher_process = multiprocessing.Process(
                target=watchertask, args=(self,)
            )
            self.watcher_process.daemon = True
            self.watcher_process.name = "watcher_process"
            self.watcher_process.start()
            self.may_do_work.set()
            self.is_done_analyzing.clear()

        except Exception as e:

            if self.output.is_dir():
                for filename in self.output.iterdir():
                    filename.unlink()
                self.output.rmdir()

            self.may_do_work.clear()
            self.is_done_analyzing.clear()
            self.watcher_process = None

            raise RuntimeError(
                "Something went wrong when starting the watcher process, undoing changes and returning"
            ) from e

    def restart(self):
        """
        restart Restart the watcher process. Must be called when, e.g., new models have been loaded or the input or output has changed.
        """
        print("trying to restart the watcher process")
        self.stop()
        self.start()

    def pause(self):
        """
        pause Pause the watcher process.

        Raises:
            RuntimeError: When the watcher process is not running.
        """
        if self.watcher_process is not None and self.watcher_process.is_alive():
            self.is_done_analyzing.wait()  # wait for the finish event
            self.may_do_work.clear()
        else:
            raise RuntimeError("Cannot pause watcher process, is not alive anymore.")

    def go_on(self):
        """
        go_on Continue the watcher thread.

        Raises:
            RuntimeError: When the watcher process is not running anymore
        """
        if self.watcher_process is not None and self.watcher_process.is_alive():
            print("continue the watcher process")
            self.may_do_work.set()
        else:
            raise RuntimeError("Cannot continue watcher process, is not alive anymore.")

    def stop(self):
        """
        stop Stop the watcher process if it is still running.

        Raises:
            RuntimeError: When the watcher process is not running anymore
        """
        if self.watcher_process is not None and self.watcher_process.is_alive():
            print("trying to stop the watcher process")
            flag_set = self.is_done_analyzing.wait(timeout=30)

            if flag_set is False:
                warnings.warn("stop timeout expired, terminating watcher process now.")

            try:
                self.watcher_process.terminate()
                self.watcher_process.join()
                self.watcher_process.close()
                self.watcher_process = None
                self.may_do_work.clear()
                self.is_done_analyzing.set()
            except Exception as e:
                raise RuntimeError(
                    "Something went wrong when trying to stop the watcher process"
                ) from e

            with open(self.output / self.batchfile_name, "w") as batch_info:
                yaml.safe_dump(
                    {
                        "first": self.first_analyzed.value,
                        "last": self.last_analyzed.value,
                    },
                    batch_info,
                )
        else:
            raise RuntimeError("Cannot stop watcher process, is not alive anymore.")

    def change_analyzer(
        self,
        model_name: str,
        preprocessor_config: dict = None,
        model_config: dict = None,
        recording_config: dict = None,
        species_predictor_config: dict = None,
        pattern: str = ".wav",
        check_time: int = 1,
        delete_recordings: str = "never",
    ):
        """
        change_analyzer Change classifier model to the one indicated by name.
        The given model name must correspond to the name of a folder in the
        iSparrow models directory created upon install. A clean-up method is
        run after model change to compensate any loss of analysis data that
        may occur during the restart of the watcher process with a different
        model.

        Args:
            model_name (str): Name of the model to be used
            preprocessor_config (dict, optional): Parameters for preprocessor given as key(str): value. If empty, default parameters of the preprocessor will be used. Defaults to {}.
            model_config (dict, optional): Parameters for the model given as key(str): value. If empty, default parameters of the model will be used. Defaults to {}.
            recording_config (dict, optional): Parameters for the underlyin SparrowRecording object. If empty, default parameters of the recording will be used. Defaults to {}.
            species_predictor_config (dict, optional): _description_. If empty, default parameters of the species predictor will be used. Defaults to {}.
            Make sure the model you use is compatible with a species predictor before supplying these.
            pattern (str, optional): filename pattern to look for. defaults to '.wav'.
            check_time(int, optional): Sleep time of the watcher between checks for new files in seconds. Defaults to 1.
            delete_recordings(str, optional): Mode for data clean up. Can be one of "never" or "always".
                                            "never" keeps recordings around indefinitely. 'always' deletes the recording
                                            immediatelly after analysis. Defaults to 'never'.

        Raises:
            ValueError: _description_
            RuntimeError: _description_
        """

        if self.watcher_process is None or self.is_running is False:
            raise RuntimeError("Watcher not running, cannot change analyzer")

        # import and build new model, pause the analyzer process,
        # change the model, resume the analyzer
        if preprocessor_config is None:
            preprocessor_config = {}

        if model_config is None:
            model_config = {}

        if recording_config is None:
            recording_config = {}

        if species_predictor_config is None:
            species_predictor_config = {}

        if (self.model_dir / model_name).is_dir() is False:
            raise ValueError("Given model name does not exist in model dir.")

        with self._backup_and_restore_state() as old_state:
            self.model_name = model_name
            self.preprocessor_config = preprocessor_config
            self.model_config = model_config
            self.recording_config = recording_config
            self.species_predictor_config = species_predictor_config
            self.pattern = pattern
            self.check_time = check_time
            self.delete_recordings = delete_recordings

            self.restart()

            try:
                while self.last_analyzed.value <= self.first_analyzed.value:
                    sleep(5)
                self.clean_up()

            except Exception as e:
                status = (
                    "still running"
                    if self.is_running
                    else "not running, any changes have been undone."
                )

                cause = e.__cause__ if e.__cause__ is not None else e

                if self.is_running is False:
                    self.restore_old_state(old_state)
                    self.may_do_work.clear()
                    self.is_done_analyzing.set()
                    self.output = Path(self.outdir) / Path(
                        datetime.now().strftime("%y%m%d_%H%M%S")
                    )
                raise RuntimeError(
                    f"Error when cleaning up data after analyzer change, watcher is {status}. The cause was {cause}. This error may have lead to corrupt data in newly created analysis files."
                ) from e

    def _get_clean_up_limits(self, older_output: str, newer_output: str) -> tuple:
        """
        _get_clean_up_limits Determine the lower and upper time limit for the clean up of the older output directory.

        Args:
            older_output (str): Older output folder that is actually cleaned up.
            newer_output (str): Newer output folder that is used to determine the upper time limit for the clean up.

        Raises:
            RuntimeError: When the newer output directory is not the currently worked on, but also has no batch info file.

        Returns:
            tuple: (lower time limit, upper time limit) pair of timestamps to use for the clean up.
        """
        with open(older_output / self.batchfile_name, "r") as batch_info:
            lower_limit = yaml.safe_load(batch_info)["last"]

        if newer_output is None:
            upper_limit = int(datetime.now().timestamp())

        elif Path(newer_output / self.batchfile_name).is_file():
            with open(newer_output / self.batchfile_name, "r") as batch_info:
                upper_limit = yaml.safe_load(batch_info)["first"]

        elif newer_output != self.output:
            raise RuntimeError(
                f"{newer_output} is not the current output directory {self.output} but has no batchinfo.yml file."
            )

        else:
            upper_limit = self.first_analyzed.value
        return lower_limit, upper_limit

    def _clean_up_between(self, older_output: str, newer_output: str):
        """
        _clean_up_between Run clean up on the older output directory between the last analyzed file and the first analyzed file in the newer output directory.
                          This function assumes that older_output and newer_output are consecutive output directories of the watcher process. Passing it
                          non-consecutive directories is undefined and may lead to unexpected results.
                          If newer_output is None, the current time is used as upper limit and all files in the older output directory are analyzed that have
                          not been analyzed by the current process.

        Args:
            older_output (str): Older output directory. This is done one that gets cleaned up.
            newer_output (str): Newer output directory. This is used to determine the upper limit time for the clean up.
        """
        if older_output == self.output and self.is_running:
            warnings.warn(
                "Cannot clean up current output directory while watcher is running"
            )
            return

        with open(older_output / "config.yml", "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        lower_limit, upper_limit = self._get_clean_up_limits(older_output, newer_output)

        input_folder = Path(cfg["Analysis"]["input"])
        outputfolder = cfg["Analysis"]["output"]

        audiofiles = [
            f
            for f in input_folder.iterdir()
            if f.suffix == cfg["Analysis"]["pattern"]
            and not Path(outputfolder, f"results_{f.stem}.csv").is_file()
            and lower_limit < f.stat().st_ctime < upper_limit
        ]

        if len(audiofiles) > 0:
            recording = self._set_up_recording(
                cfg["Analysis"]["model_name"],
                cfg["Analysis"]["Recording"],
                cfg["Analysis"]["SpeciesPredictor"],
                cfg["Analysis"]["Model"],
                cfg["Analysis"]["Preprocessor"],
            )

            for audiofile in audiofiles:
                recording.path = audiofile
                recording.analyzed = False
                recording.analyze()
                results = recording.detections
                self.save_results(outputfolder, results, suffix=str(audiofile.stem))

                if cfg["Analysis"]["delete_recordings"] == "always":
                    audiofile.unlink()

            with open(older_output / "missings.txt", "w") as missing:
                for audiofile in audiofiles:
                    missing.write(f"{audiofile}\n")

    def clean_up(self):
        """
        clean_up Run cleanup on the all the output directories of the watcher process that reside in the current output base directory.

        """
        folders = sorted(
            filter(lambda f: f.is_file() is False, list(self.outdir.iterdir())),
            key=lambda x: x.stat().st_ctime,
        )

        folders.append(None)  # add dummy to include the last folder

        if folders == [
            None,
        ]:
            raise RuntimeError("No output folders found to clean up")
        else:
            for i in range(1, len(folders)):
                self._clean_up_between(folders[i - 1], folders[i])
