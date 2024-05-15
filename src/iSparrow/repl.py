from iSparrow import SparrowWatcher
import iSparrow.sparrow_setup as sps
from iSparrow.utils import read_yaml, update_dict_leafs_recursive

from pathlib import Path
from platformdirs import user_config_dir
import cmd


def process_line_into_kwargs(line: str, keywords: list = None):

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
    prompt = "(iSparrow)"
    intro = "Welcome to iSparrow! Type help or ? to list commands.\n"

    def __init__(self):
        super().__init__()
        self.watcher = None

    def do_help(self, line: str):
        print("Commands: ")
        print("set_up: set up iSparrow for usage")
        print("start: start a watcher for analyzing incoming files in a directory")
        print("stop: stop a previously started watcher")
        print("pause: pause a running watcher")
        print("continue: continue a paused watcher")
        print("restart: restart an existing watcher")
        print("exit: leave this shell.")
        print(
            "Commands can have optional arguments. Use 'help <command>' to get more information on a specific command."
        )

    def process_arguments(
        self,
        line: str,
        keywords: list,
        do_no_inputs: callable = lambda s: None,
        do_with_inputs: callable = lambda s: None,
        do_with_failure: callable = lambda s, e: None,
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
                f"Invalid input. Expected {len(keywords)} blocks of the form --name=<arg>"
            )
            return inputs, True
        elif len(inputs) == 0:
            print("No config file provided, falling back to default")
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

    def do_set_up(self, line: str):
        """
        do_set_up Setup iSparrow. This creates a `iSparrow` folder in the user's home directory and copies the default configuration files into os_standard_config_dir/iSparrow. If a custom configuration file is provided, it will be used instead of the default.

        Args:
            line (str): Optional path relative to the user's home directory to a custom configuration file. The file must be a yaml file with the same structure as the default configuration file.
        """
        self.process_arguments(
            line,
            ["--cfg"],
            do_no_inputs=lambda self, inputs: sps.set_up_sparrow(None),
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
        if Path(user_config_dir(), "iSparrow").exists() is False:
            print("No installation found - please run the setup command first")
            return

        cfg = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "default.yml")

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
            ),
        )

        if error is True:
            return

        cfgpath = Path(args["cfg"]).expanduser().resolve() if "cfg" in args else None

        if self.watcher is None:

            if cfgpath is not None:
                custom_cfg = read_yaml(cfgpath)
                update_dict_leafs_recursive(cfg, custom_cfg)

            try:
                self.watcher = SparrowWatcher(
                    indir=Path(cfg["Data"]["input"]).expanduser().resolve(),
                    outdir=Path(cfg["Data"]["output"]).expanduser().resolve(),
                    model_dir=Path(cfg["Analysis"]["model_dir"]).expanduser().resolve(),
                    model_name=cfg["Analysis"]["modelname"],
                    model_config=cfg["Analysis"]["Model"],
                    preprocessor_config=cfg["Data"]["Preprocessor"],
                    recording_config=cfg["Analysis"]["Recording"],
                    species_predictor_config=cfg["Analysis"].get(
                        "SpeciesPredictor", None
                    ),
                    pattern=cfg["Analysis"]["pattern"],
                    check_time=cfg["Analysis"]["check_time"],
                    delete_recordings=cfg["Analysis"]["delete_recordings"],
                )
            except Exception as e:
                print(
                    f"An error occured while trying to build the watcher: {e} caused by {e.__cause__}"
                )
                return

            try:
                self.watcher.start()
            except Exception as e:
                print(
                    f"Something went wrong while trying to start the watcher: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed.",
                )

        elif self.watcher.is_running:
            print(
                "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters."
            )
        else:
            print(
                "It appears that there is a watcher process that is not running. Trying to start with current parameters. Use  the 'change_analyzer' command to change the parameters."
            )
            try:
                self.watcher.start()
            except RuntimeError as e:
                print(
                    f"Something went wrong while trying to start the watcher process: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed."
                )

    def do_stop(self, line: str):
        """
        do_stop Stop a running sparrow watcher process.
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        def handle_failure(s: cmd, e: Exception):
            print(
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

    def do_pause(self, line: str):
        """
        do_pause Pause a running sparrow watcher process.
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print("Cannot pause watcher, no watcher present"),
            do_is_running=lambda _: self.watcher.pause(),
            do_is_sleeping=lambda _: print("Cannot pause watcher, is already sleeping"),
            do_else=lambda self: print("Cannot pause watcher, is not running"),
            do_failure=lambda _, e: print(
                f"Could not pause watcher: {e} caused by {e.__cause__}"
            ),
        )

    def do_continue(self, line: str):
        """
        do_continue Continue a paused sparrow watcher from where it was paused.
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print("Cannot continue watcher, no watcher present"),
            do_is_running=lambda _: print("Cannot continue watcher, is not sleeping"),
            do_is_sleeping=lambda self: self.watcher.go_on(),
            do_else=lambda _: print("Cannot continue watcher, is not running"),
            do_failure=lambda _, e: print(
                f"Could not continue watcher: {e} caused by {e.__cause__}"
            ),
        )

    def do_restart(self, line: str):
        """
        do_restart Restart an existing sparrow watcher with the same parameters
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        self.dispatch_on_watcher(
            do_is_none=lambda _: print("Cannot restart watcher, no watcher present"),
            do_is_sleeping=lambda _: print(
                "Cannot restart watcher, is sleeping and must be continued first"
            ),
            do_is_running=lambda self: self.watcher.restart(),
            do_else=lambda _: print("Cannot restart watcher, is not running"),
            do_failure=lambda _, e: print(
                f"Could not restart watcher: {e} caused by {e.__cause__}"
            ),
        )

    def do_exit(self, line: str):
        """
        do_exit Leave the sparrow shell
        """
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return
        print("Exiting sparrow shell")
        return True