from iSparrow import SparrowWatcher
import iSparrow.sparrow_setup as sps
from iSparrow.utils import read_yaml, update_dict_leafs_recursive

from pathlib import Path
from platformdirs import user_config_dir
import cmd
import multiprocessing
import os
from contextlib import contextmanager


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

    def do_help(self, line):
        print("Commands: ")
        print("set_up")
        print("start")
        print("stop")
        print("exit")
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
    ) -> dict:
        inputs = None
        try:
            inputs = process_line_into_kwargs(line, keywords)
        except Exception as e:
            do_with_failure(self, inputs, e)
            return {}

        if len(inputs) > len(keywords):
            print(
                f"Invalid input. Expected {len(keywords)} blocks of the form --name=<arg>"
            )
            return {}
        elif len(inputs) == 0:
            print("No config file provided, falling back to default")
            try:
                do_no_inputs(self, inputs)
            except Exception as e:
                do_with_failure(self, inputs, e)
        else:
            try:
                do_with_inputs(self, inputs)
            except Exception as e:
                do_with_failure(self, inputs, e)

    def dispatch_on_watcher(
        self,
        do_is_none: callable = lambda s: None,
        do_is_sleeping: callable = lambda s: None,
        do_is_running: callable = lambda s: None,
        do_else: callable = lambda s: None,
        do_failure: callable = lambda s, e: None,
    ):
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

    def do_set_up(self, line):

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

    def do_start(self, line):

        if Path(user_config_dir(), "iSparrow").exists() is False:
            print("No installation found - please run the setup command first")
            return

        cfg = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "default.yml")

        cfgpath = None

        def assign_cfgpath(s, inputs):
            nonlocal cfgpath
            cfgpath = Path(inputs["cfg"]).expanduser().resolve()

        ret = self.process_arguments(
            line,
            ["--cfg"],
            do_no_inputs=lambda _, __: print(
                "No config file provided, falling back to default"
            ),
            do_with_inputs=assign_cfgpath,
            do_with_failure=lambda _, __, e: print(
                "Something in the start command parsing went wrong. Check your passed commands. Caused by: ",
                e,
            ),
        )

        if ret == {}:
            return

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
            except RuntimeError as e:
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

    def do_stop(self, line):

        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return

        def handle_failure(s, e):
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

    def do_pause(self, line):
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

    def do_continue(self, line):
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

    def do_restart(self, line):
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

    def do_exit(self, line):
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
            return
        print("Exiting sparrow shell")
        return True

    def do_check(self, line):
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
        elif self.watcher is None:
            print("No watcher present, cannot check status")
        else:
            print("is running:", self.watcher.is_running)
            print("is sleeping:", self.watcher.is_sleeping)
            print("may do work:", self.watcher.may_do_work.is_set())

    def do_change_analyzer(self, line):
        if self.watcher is None:
            print("No watcher present, cannot change analyzer")
        elif self.watcher.is_running is False:
            print("Cannot change analyzer, watcher is not running")
        elif self.watcher.is_sleeping:
            print("Cannot change analyzer, watcher is sleeping")
        else:
            inputs = process_line_into_kwargs(
                line,
                ["--cfg"],
            )

            cfg = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "default.yml")

            cfgpath = None

            if len(inputs) > 1:
                print("Invalid input. Expected: change_analyzer --cfg=<config_file>")
                return
            elif len(inputs) == 1:
                cfgpath = Path(inputs["cfg"]).expanduser().resolve()
            elif len(inputs) == 0:
                cfgpath = None
            else:
                print("No config file provided, cannot change analyzer")
                return

            if cfgpath is not None:
                custom_cfg = read_yaml(cfgpath)
                update_dict_leafs_recursive(cfg, custom_cfg)
            try:
                self.watcher.change_analyzer(
                    model_name=cfg["Analysis"]["modelname"],
                    preprocessor_config=cfg["Data"]["Preprocessor"],
                    model_config=cfg["Analysis"]["Model"],
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
                    f"An error occured while trying to change the analyzer: {e} caused by {e.__cause__}"
                )

    def postloop(self):
        if self.watcher is not None:
            try:
                print("stopping watcher")
                self.watcher.stop()
            except Exception as e:
                print("Could not stop watcher", e, "caused by: ", e.__cause__)
        else:
            print("No watcher was present, exiting")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    SparrowCmd().cmdloop()
