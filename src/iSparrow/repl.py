from pathlib import Path
from platformdirs import user_config_dir, user_cache_dir
import cmd
import time
import traceback

from iSparrow import SparrowWatcher
import iSparrow.sparrow_setup as sps
from iSparrow.utils import read_yaml, update_dict_leafs_recursive


def process_line_into_kwargs(line: str, keywords: list = None) -> dict:
    """
    process_line_into_kwargs Process string into keyword argument dictionary

    Args:
        line (str): raw string input that contains keyword arguments
        keywords (list, optional): list of kwargs to look for in the input line. Defaults to None.

    Raises:
        ValueError: When the input does not adhere to the --name=<arg> structure
        ValueError: When the keywords are not provided in the input line
        ValueError: When an expected keyword is not found in the input line

    Returns:
        dcit: dictionary with keyword: value pairs, where the values are strings
    """
    if line == "":
        return {}

    if "=" not in line:
        raise ValueError("Invalid input. Expected options structure is --name=<arg>")

    if keywords is None or len(keywords) == 0:
        raise ValueError("Keywords must be provided with passed line")

    for k in keywords:
        if k not in line:
            raise ValueError(f"Keyword {k} not found in passed line")

    kwargs = {
        name.lstrip("-"): key
        for part in line.split(" ")
        if "=" in part
        for name, key in [part.split("=")]
    }

    return kwargs


class SparrowCmd(cmd.Cmd):
    """
    SparrowCmd is a command-line interface for interacting with a SparrowWatcher instance.

    This class provides a set of commands for setting up, starting, stopping, and managing a watcher process that analyzes incoming files in a directory. It also provides commands for getting the status of the watcher process and the current setup of iSparrow.

    Attributes:
        prompt (str): The prompt string displayed in the command-line interface.
        intro (str): The introductory message displayed when the command-line interface starts.
        watcher: The watcher process that is being managed.
        running (bool): Indicates whether the command-line interface is currently running.
    """

    prompt = "(iSparrow)"
    intro = "Welcome to iSparrow! Type help or ? to list commands.\n"

    def __init__(self):
        """
        __init__ Create a new SparrowCmd instance.

        """
        super().__init__()
        self.watcher = None
        self.running = True

    def update_parameters(self, cfgpath: str = None):
        """
        update_parameters Update watcher parameter dictionaries read from yaml files.
                        A default configuration file is used if no custom configuration file is provided.
                        Otherwise, the default config for the desired model is updated with the custom config.

        Args:
            cfgpath (str, optional): Path to a config file. Defaults to None.

        Returns:
            _type_: _description_
        """
        folders = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "install.yml")[
            "Directories"
        ]

        model_dir = Path(folders["models"]).expanduser()

        if cfgpath is not None:
            custom_config = read_yaml(cfgpath)
        else:
            custom_config = read_yaml(
                model_dir / Path("birdnet_default") / "default.yml"
            )

        fallback_modelname = (
            self.watcher.model_name if self.watcher is not None else "birdnet_default"
        )

        modelname = (
            Path(custom_config["Analysis"]["modelname"])
            if "modelname" in custom_config["Analysis"]
            else fallback_modelname
        )

        config = read_yaml(model_dir / modelname / "default.yml")

        update_dict_leafs_recursive(config, custom_config)

        return config

    def process_arguments(
        self,
        line: str,
        keywords: list,
        do_no_inputs: callable = lambda s: None,
        do_with_inputs: callable = lambda s: None,
        do_with_failure: callable = lambda s, args, e: None,
    ) -> tuple:
        """
        process_arguments Process the argument string of a command into its individual parts, based on a '--name=<arg>' structure. Depending on the input, different actions are taken as given in the arguments.
        Args:
            line (str): Argument string
            keywords (list): expected argument names in the form of '--name=<arg>'
            do_no_inputs (callable, optional): Function to call when no inputs are given. Defaults to lambda s:None (do nothing).
            do_with_inputs (callable, optional): Function to call with the correct input structure. Defaults to lambda s:None.
            do_with_failure (callable, optional): Function to call when an exception is thrown during processing. Defaults to lambda s, e: None.

        Returns:
            tuple: _description_
        """
        inputs = None
        try:
            inputs = process_line_into_kwargs(line, keywords)
        except Exception as e:
            do_with_failure(self, inputs, e)
            return inputs, True

        if len(inputs) > len(keywords):
            print(
                f"Invalid input. Expected {len(keywords)} blocks of the form --name=<arg> with names {keywords}"
            )
            return inputs, True
        elif len(inputs) == 0:
            try:
                do_no_inputs(self, inputs)
                return inputs, False
            except Exception as e:
                do_with_failure(self, inputs, e)
                return inputs, True
        else:
            try:
                do_with_inputs(self, inputs)
                return inputs, False
            except Exception as e:
                do_with_failure(self, inputs, e)
                return inputs, True

    def dispatch_on_watcher(
        self,
        do_is_none: callable = lambda s: None,
        do_is_sleeping: callable = lambda s: None,
        do_is_running: callable = lambda s: None,
        do_else: callable = lambda s: None,
        do_failure: callable = lambda s, e: None,
    ):
        """
        dispatch_on_watcher Process different watcher states, using different callables. Useful for error catching and handling when a command should be issued to a watcher.

        Args:
            do_is_none (callable, optional): Function to call when there is no watcher. Defaults to lambda s:None. (do nothing)
            do_is_sleeping (callable, optional): Function to call when the watcher is sleeping. Defaults to lambda s:None.
            do_is_running (callable, optional): Function to call when the watcher is running. Defaults to lambda s:None.
            do_else (callable, optional): Function to call when the watcher has been stopped or has been created but is not running. Defaults to lambda s:None.
            do_failure (callable, optional): Function to call upon an exception occuring in any of the above. Defaults to lambda s, e: None (do nothing). Make sure to override this to get proper error handling.
        """
        if self.watcher is None:
            try:
                do_is_none(self)
            except Exception as e:
                do_failure(self, e)
        elif self.watcher.is_sleeping:
            try:
                do_is_sleeping(self)
            except Exception as e:
                do_failure(self, e)
        elif self.watcher.is_running:
            try:
                do_is_running(self)
            except Exception as e:
                do_failure(self, e)
        else:
            try:
                do_else(self)
            except Exception as e:
                do_failure(self, e)

    def print_error(self, message: str):
        """
        print_error Print error message and traceback. Used for providing information about exceptions.

        Args:
            message (str): Error message to print
        """
        print(
            message,
            flush=True,
        )
        print("Traceback: ")
        traceback.print_exc()

    def handle_exit(self):
        """
        handle_exit  Stops the watcher if it is running upon exiting the shell if it is running.
        """
        self.running = False
        if self.watcher is not None and self.watcher.is_running:
            try:  # Try to stop the watcher
                self.watcher.stop()
                self.wait_for_watcher_event(
                    lambda s: s.watcher.is_running is False, limit=20, waiting_time=3
                )
            except Exception as e:
                self.print_error(
                    f"Could not stop watcher: {e} caused by {e.__cause__}. Watcher process will be killed now."
                )

                if self.watcher.is_running:
                    self.watcher.watcher_process.kill()

    def wait_for_watcher_event(
        self, event: callable, limit: int = 10, waiting_time: int = 5
    ):
        """
        wait_for_watcher_event Wait for  defined event happening to the watcher process, and block the caller until then.

        Args:
            event (callable): Event to wait for. Must be a function that takes the current instance of the shell as an argument and returns a boolean.
            limit (int, optional): Timeout limit for the waiting. Timeout in seconds is limit * waiting_time. Defaults to 10.
            waiting_time (int, optional): Waiting time for each test. Defaults to 5.
        """
        i = 0
        while True:
            if event(self):
                break
            elif i > limit:
                print(
                    "Error while performing watcher interaction: Timeout.", flush=True
                )
                break
            else:
                time.sleep(waiting_time)
                i += 1

    # Command definitions

    def do_help(self, line: str):
        """
        do_help Print help strings for available commands

        Args:
            line (str): dummy, no arguments expected
        """
        print("Commands: ")
        print(
            "set_up: set up iSparrow for usage. Usage: 'set_up --cfg=<path>'. When no argumnet is provided, the default is used."
        )
        print(
            "start: start a watcher for analyzing incoming files in a directory. Usage: 'start --cfg=<path>'. When no argumnet is provided, the default from birdnetlib is used."
        )
        print("stop: stop a previously started watcher")
        print("pause: pause a running watcher")
        print("continue: continue a paused watcher")
        print("restart: restart an existing watcher")
        print("change analyzer: change the analyzer of a running watcher")
        print(
            "cleanup: cleanup the output directory of the watcher, assuring data consistency"
        )
        print("status: get the current status of the watcher process")
        print("get_setup_info: get information about the current setup of iSparrow")
        print("exit: leave this shell.")
        print(
            "Commands can have optional arguments. Use 'help <command>' to get more information on a specific command."
        )

    def do_set_up(self, line: str):
        """
        do_set_up Setup iSparrow. This creates a `iSparrow` folder in the user's home directory and copies the default configuration files into os_standard_config_dir/iSparrow. If a custom configuration file is provided, it will be used instead of the default.

        Args:
            line (str): Optional path relative to the user's home directory to a custom configuration file. The file must be a yaml file with the same structure as the default configuration file.
        """

        def do_no_inputs(_, __):
            print("No config file provided, falling back to default\n")
            sps.set_up_sparrow(None)

        self.process_arguments(
            line,
            ["--cfg"],
            do_no_inputs=lambda self, inputs: do_no_inputs(self, inputs),
            do_with_inputs=lambda self, inputs: sps.set_up_sparrow(
                Path(inputs["cfg"]).expanduser().resolve()
            ),
            do_with_failure=lambda self, inputs, e: print(
                "Could not set up iSparrow", e, "caused by: ", e.__cause__
            ),
        )

    def do_start(self, line: str):
        """
        do_start Start a new sparrow watcher process. Only can be started if no other watcher is currently running.

        Args:
            line (str): optional argument --cfg=<path> to provide a custom configuration file.
        """

        # helper closures to use with self.dispatch_on_watcher. No exception handling is necesssary in the functions below,
        # since this is handled by the dispatch_on_watcher method.
        def build_watcher(cfg: dict):
            self.watcher = SparrowWatcher(
                indir=Path(cfg["Data"]["input"]).expanduser().resolve(),
                outdir=Path(cfg["Data"]["output"]).expanduser().resolve(),
                model_dir=Path(cfg["Analysis"]["model_dir"]).expanduser().resolve(),
                model_name=cfg["Analysis"]["modelname"],
                model_config=cfg["Analysis"]["Model"],
                preprocessor_config=cfg["Data"]["Preprocessor"],
                recording_config=cfg["Analysis"]["Recording"],
                species_predictor_config=cfg["Analysis"].get("SpeciesPredictor", None),
                pattern=cfg["Analysis"]["pattern"],
                check_time=cfg["Analysis"]["check_time"],
                delete_recordings=cfg["Analysis"]["delete_recordings"],
            )

        def start_watcher():
            self.watcher.start()
            self.wait_for_watcher_event(
                lambda s: s.watcher.is_running, limit=20, waiting_time=3
            )

        # actual build and start process
        if Path(user_config_dir(), "iSparrow").exists() is False:
            print("No installation found - please run the setup command first")
            return

        args, error = self.process_arguments(
            line,
            ["--cfg"],
            do_no_inputs=lambda _, __: print(
                "No config file provided, falling back to default"
            ),
            do_with_inputs=lambda _, __: None,
            do_with_failure=lambda _, __, e: print(
                "Something in the start command parsing went wrong. Check your passed commands. Caused by: ",
                e,
                flush=True,
            ),
        )

        if error is True:
            print("An error occurred while processing arguments.")
            print("traceback: ")
            traceback.print_exc()
            return

        cfgpath = Path(args["cfg"]).expanduser().resolve() if "cfg" in args else None

        cfg = None
        try:
            cfg = self.update_parameters(cfgpath)
        except Exception as e:
            self.print_error(
                f"An error occured while trying to update the parameters: {e} caused by {e.__cause__}"
            )
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: build_watcher(cfg),
            do_is_sleeping=lambda _: lambda _: print(
                "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters.",
                flush=True,
            ),
            do_is_running=lambda _: print(
                "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters.",
                flush=True,
            ),
            do_else=lambda _: print(
                "It appears that there is a watcher process that is not running. Trying to start with current parameters. Use  the 'change_analyzer' command to change the parameters.",
                flush=True,
            ),
            do_failure=lambda _, e: self.print_error(
                f"An error occured while trying to build the watcher: {e} caused by {e.__cause__}"
            ),
        )

        self.dispatch_on_watcher(
            do_is_none=lambda _: print(
                "There seems to be no watcher. Cannot start.",
                flush=True,
            ),
            do_is_sleeping=lambda _: print(
                "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters.",
                flush=True,
            ),
            do_is_running=lambda _: print(
                "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters.",
                flush=True,
            ),
            do_else=lambda _: start_watcher(),
            do_failure=lambda _, e: self.print_error(
                f"Something went wrong while trying to start the watcher: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed."
            ),
        )

    def do_stop(self, line: str):
        """
        do_stop Stop a running sparrow watcher process.
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        def handle_failure(s: cmd, e: Exception):
            self.print_error(
                f"Could not stop watcher: {e} caused by {e.__cause__}. Watcher process will be killed now and all resources released. This may have left data in a corrupt state. A new watcher must be started if this session is to be continued."
            )

            if s.watcher.is_running:
                s.watcher.watcher_process.kill()
            s.watcher = None

        self.dispatch_on_watcher(
            do_is_none=lambda _: print("Cannot stop watcher, no watcher present"),
            do_is_sleeping=lambda self: self.watcher.stop(),
            do_is_running=lambda self: self.watcher.stop(),
            do_else=lambda _: print("Cannot stop watcher, is not running"),
            do_failure=handle_failure,
        )

        if self.watcher is not None:
            self.wait_for_watcher_event(
                lambda s: s.watcher.is_running is False, limit=20, waiting_time=3
            )

    def do_cleanup(self, line: str):
        """
        do_cleanup Run the cleanup method of the watcher process to assure data consistency

        Args:
            line (str): Empty string, no arguments expected
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print(
                "Cannot run cleanup, no watcher present", flush=True
            ),
            do_is_sleeping=lambda self: self.watcher.clean_up(),
            do_is_running=lambda self: self.watcher.clean_up(),
            do_else=lambda self: self.watcher.clean_up(),
            do_failure=lambda s, e: self.print_error(
                f"Error while running cleanup: {e}"
            ),
        )

    def do_exit(self, line: str):
        """
        do_exit Leave the sparrow shell
        """
        self.running = False
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        print("Exiting sparrow shell")
        return True

    def do_pause(self, line: str):
        """
        do_pause Pause the watcher process.

        Args:
            line (str): Empty string, no arguments expected
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.", flush=True)
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print(
                "Cannot pause watcher, no watcher present", flush=True
            ),
            do_is_running=lambda _: self.watcher.pause(),
            do_is_sleeping=lambda _: print(
                "Cannot pause watcher, is already sleeping", flush=True
            ),
            do_else=lambda self: print(
                "Cannot pause watcher, is not running", flush=True
            ),
            do_failure=lambda _, e: self.print_error(
                f"Could not pause watcher: {e} caused by {e.__cause__}",
            ),
        )

    def do_continue(self, line: str):
        """
        do_continue Continue the watcher process after it has been paused.

        Args:
            line (str): Empty string, no arguments expected
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.", flush=True)
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print(
                "Cannot continue watcher, no watcher present", flush=True
            ),
            do_is_running=lambda _: print(
                "Cannot continue watcher, is not sleeping", flush=True
            ),
            do_is_sleeping=lambda self: self.watcher.go_on(),
            do_else=lambda _: print(
                "Cannot continue watcher, is not running", flush=True
            ),
            do_failure=lambda _, e: self.print_error(
                f"Could not continue watcher: {e} caused by {e.__cause__}"
            ),
        )

    def do_restart(self, line: str):
        """
        do_restart Restart the watcher process.

        Args:
            line (str): Empty string, no arguments expected
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.", flush=True)
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print(
                "Cannot restart watcher, no watcher present", flush=True
            ),
            do_is_sleeping=lambda _: print(
                "Cannot restart watcher, is sleeping and must be continued first",
                flush=True,
            ),
            do_is_running=lambda self: self.watcher.restart(),
            do_else=lambda _: print(
                "Cannot restart watcher, is not running", flush=True
            ),
            do_failure=lambda _, e: self.print_error(
                f"Could not restart watcher: {e} caused by {e.__cause__}"
            ),
        )

    def do_status(self, line: str):
        """
        do_status Get the current status of the watcher process.

        Args:
            line (str): Empty string, no arguments expected
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.", flush=True)
        elif self.watcher is None:
            print("No watcher present, cannot check status", flush=True)
        else:
            print("model name", self.watcher.model_name, flush=True)
            print("current input directory", self.watcher.input_directory, flush=True)
            print("current output directory", self.watcher.output_directory, flush=True)
            print("is running:", self.watcher.is_running, flush=True)
            print("is sleeping:", self.watcher.is_sleeping, flush=True)
            print("may do work:", self.watcher.may_do_work.is_set(), flush=True)
            print(
                "is done analying: ",
                self.watcher.is_done_analyzing.is_set(),
                flush=True,
            )

    def do_get_setup_info(self, line: str):
        """
        do_get_setup_info Get information about the current setup of iSparrow. If no setup information is found, the cache and config directories are listed.
        Args:
            line (str): Empty string, no arguments expected
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.", flush=True)
        elif Path(user_config_dir(), "iSparrow", "install.yml").is_file() is False:
            print(
                "cache directories: ",
                [
                    f.expanduser()
                    for f in Path(user_cache_dir()).iterdir()
                    if "iSparrow" in str(f)
                ],
                flush=True,
            )
            print(
                "config directories: ",
                [
                    f.expanduser()
                    for f in Path(user_config_dir()).iterdir()
                    if "iSparrow" in str(f)
                ],
                flush=True,
            )
            print("No further setup information found", flush=True)
        else:
            print(
                "cache directories: ",
                [
                    f.expanduser()
                    for f in Path(user_cache_dir()).iterdir()
                    if "iSparrow" in str(f)
                ],
                flush=True,
            )
            print(
                "config directories: ",
                [
                    f.expanduser()
                    for f in Path(user_config_dir()).iterdir()
                    if "iSparrow" in str(f)
                ],
                flush=True,
            )
            print(
                "Current setup: ",
                read_yaml(str(Path(user_config_dir(), "iSparrow", "install.yml"))),
                flush=True,
            )

    def do_change_analyzer(self, line: str):
        """
        do_change_analyzer Change the analyzer of the watcher process. This will assert data consistency in the output folder of the old analyzer.

        Args:
            line (str): Path to a custom configuration file. The file must be a yaml file with the same structure as the default configuration file.
        """

        # add a closure to encapsulate analyzer change logic
        def run_analyzer_change(cfg: str = ""):
            config = None
            try:
                config = self.update_parameters(cfg)
            except Exception as e:
                self.print_error(
                    f"An error occured while trying to update the parameters: {e} caused by {e.__cause__}"
                )

            self.watcher.change_analyzer(
                model_name=config["Analysis"]["modelname"],
                preprocessor_config=config["Data"]["Preprocessor"],
                model_config=config["Analysis"]["Model"],
                recording_config=config["Analysis"]["Recording"],
                species_predictor_config=config["Analysis"].get(
                    "SpeciesPredictor", None
                ),
                pattern=config["Analysis"]["pattern"],
                check_time=config["Analysis"]["check_time"],
                delete_recordings=config["Analysis"]["delete_recordings"],
            )

            self.wait_for_watcher_event(
                lambda s: s.watcher.is_running, limit=20, waiting_time=3
            )

        # apply the above closure to the watcher
        self.dispatch_on_watcher(
            do_is_none=lambda _: print("No watcher present, cannot change analyzer\n"),
            do_is_sleeping=lambda _: print(
                "Cannot change analyzer, watcher is sleeping\n"
            ),
            do_is_running=lambda s: s.process_arguments(
                line,
                ["--cfg"],
                do_no_inputs=lambda s: print(
                    "Cannot change analyzer, no config file provided\n"
                ),
                do_with_inputs=lambda _, kwargs: run_analyzer_change(**kwargs),
                do_with_failure=lambda s, _, e: self.print_error(
                    f"An error occured when changing analyzer: {e}, caused by {e.__cause__}\n"
                ),
            ),
            do_else=lambda _: print("Cannot change analyzer, watcher is not running\n"),
            do_failure=lambda _, e: self.print_error(
                f"An error occured when changing analyzer: {e}, caused by {e.__cause__}\n"
            ),
        )

    def emptyline(self):
        print("\n")

    def postloop(self):
        self.handle_exit()

    def postcmd(self, stop, line):
        print("\n")
        return stop

    def cmdloop(self, intro=None):
        """
        cmdloop Override of the cmd.cmdloop method to catch KeyboardInterrupts and other exceptions that might occur during the execution of the shell.

        Args:
            intro (str, optional): Intro text when starting. Defaults to None.
        """
        while self.running:
            try:
                super().cmdloop()

                while not self.watcher.exception_queue.empty():
                    e, traceback_str = self.watcher.exception_queue.get()
                    print("An error occurred in the watcher subprocess: ", e)
                    print("Traceback: ", traceback_str)
            except KeyboardInterrupt:
                print("Execution Interrupted\n")
                print("Exiting shell...\n")
                self.running = False
                break
            except Exception as e:
                print("An error occured: ", e, " caused by: ", e.__cause__)
                print("Traceback: ")
                traceback.print_exc()
                print(
                    "If you tried to modify the watcher, make sure to restart it or exit and start a new session"
                )
            finally:
                print(self.prompt, flush=True)


def run():
    import multiprocessing

    multiprocessing.set_start_method("spawn", True)
    SparrowCmd().cmdloop()
