from iSparrow import SparrowWatcher
import iSparrow.sparrow_setup as sps
from iSparrow.utils import read_yaml, update_dict_recursive
from pathlib import Path
from platformdirs import user_config_dir
import cmd
import multiprocessing


def process_line_into_kwargs(line: str, keywords: list = None):

    if line == "":
        return {}

    if "=" not in line:
        raise ValueError("Invalid input. Expected options structure is --name=<arg>")

    if keywords is None:
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

    def do_set_up(self, line):
        inputs = None
        try:
            inputs = process_line_into_kwargs(
                line,
                [
                    "--cfg=",
                ],
            )
        except Exception as e:
            print(
                "Something in the setup command parsing went wrong. Check your passed commands. Caused by: ",
                e,
            )
            return

        cfg = None

        if len(inputs) > 1:
            print("Invalid input. Expected: set_up --cfg=<config_file>")
            return
        elif len(inputs) == 1:
            cfg = Path(inputs["cfg"]).expanduser().resolve()
        elif len(inputs) == 0:
            cfg = None
            print("No config file provided, falling back to default")

        try:
            sps.set_up_sparrow(cfg)

        except Exception as e:
            print("Could not set up iSparrow", e, "caused by: ", e.__cause__)

    def do_start(self, line):

        cfg = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "default.yml")
        install_cfg = read_yaml(
            Path(user_config_dir()) / Path("iSparrow") / "install.yml"
        )

        inputs = process_line_into_kwargs(
            line,
            [
                "--cfg=",
            ],
        )

        cfgpath = None

        if len(inputs) > 1:
            print("Invalid input. Expected: start --cfg=<config_file>")
            return
        elif len(inputs) == 1:
            cfgpath = Path(inputs[0]).expanduser().resolve()
        elif len(inputs) == 0:
            cfgpath = None
        else:
            print("No config file provided, falling back to default")

        if self.watcher is None:

            if cfgpath is not None:
                custom_cfg = read_yaml(cfgpath)
                update_dict_recursive(cfg, custom_cfg)

            try:
                self.watcher = SparrowWatcher(
                    indir=Path(cfg["Data"]["input"]).expanduser().resolve(),
                    outdir=Path(cfg["Data"]["output"]).expanduser().resolve(),
                    model_dir=Path(install_cfg["Directories"]["models"])
                    .expanduser()
                    .resolve(),
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
                self.watcher = None

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
                "It appears that there is a watcher process that is not running. Trying to start"
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

        if self.watcher is None:
            print("Cannot stop watcher, no watcher present")

        elif self.watcher.is_running is False:
            print("Cannot stop watcher, is not running")
        else:
            try:
                self.watcher.stop()
            except Exception as e:
                print(
                    f"Could not stop watcher: {e} caused by {e.__cause__}. Watcher process will be killed now and all resources released. This may have left data in a corrupt state. A new watcher must be started if this session is to be continued."
                )
                self.watcher.watcher_process.kill()
                self.watcher = None

    def do_pause(self, line):
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")

        if self.watcher is None:
            print("Cannot pause watcher, no watcher present")

        elif self.watcher.is_running is False:
            print("Cannot pause watcher, is not running")
        elif self.watcher.is_sleeping:
            print("Cannot pause watcher, is already sleeping")
        else:
            try:
                self.watcher.pause()
            except Exception as e:
                print(f"Could not pause watcher: {e} caused by {e.__cause__}")

    def do_continue(self, line):
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")
        if self.watcher is None:
            print("Cannot continue watcher, no watcher present")
        elif self.watcher.is_running is False:
            print("Cannot continue watcher, is not running")
        elif self.watcher.is_sleeping is False:
            print("Cannot continue watcher, is not sleeping")
        else:
            try:
                self.watcher.go_on()
            except Exception as e:
                print(f"Could not continue watcher: {e} caused by {e.__cause__}")

    def do_restart(self, line):
        if len(line) > 0:
            print("Invalid input. Expected no arguments.")

        if self.watcher is None:
            print("Cannot restart watcher, no watcher present")

        elif self.watcher.is_running is False:
            print("Cannot restart watcher, is not running")
        elif self.watcher.is_sleeping is False:
            print("Cannot restart watcher, is sleeping and must be continued first")
        else:
            try:
                self.watcher.restart()
            except Exception as e:
                print(f"Could not restart watcher: {e} caused by {e.__cause__}")

    def do_exit(self, line):
        print("Exiting sparrow shell")
        return True

    def change_analyzer(self, line):
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
                cfgpath = Path(inputs[0]).expanduser().resolve()
            elif len(inputs) == 0:
                cfgpath = None
            else:
                print("No config file provided, cannot change analyzer")
                return

            if cfgpath is not None:
                custom_cfg = read_yaml(cfgpath)
                update_dict_recursive(cfg, custom_cfg)
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
