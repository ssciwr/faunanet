from iSparrow import SparrowWatcher
from iSparrow import set_up_sparrow, SPARROW_HOME, SPARROW_MODELS
from utils import read_yaml, update_dict_recursive
from pathlib import Path
from platformdirs import user_config_dir
import cmd


def process_line(line: str):
    print("passed line: ", line)
    return line.split("=")


class SparrowCmd(cmd.Cmd):
    prompt = "(iSparrow)"
    intro = "Welcome to iSparrow! Type help or ? to list commands.\n"

    def __init__(self):
        super().__init__()
        self.watcher = None
        self.input = None
        self.output = None
        self.models = None

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
        print("Setting up iSparrow")

        inputs = process_line(line)

        cfg = None

        if len(inputs) > 2:
            print("Invalid input. Expected: set_up <config_file>")
            return
        elif len(inputs) == 2:
            cfg = Path(inputs[1])
        elif len(inputs) == 0:
            cfg = None
        else:
            print("No config file provided, falling back to default")

        try:
            set_up_sparrow(cfg)
            global HOME, MODELS
            HOME = SPARROW_HOME
            MODELS = SPARROW_MODELS

        except Exception as e:
            print("Could not set up iSparrow", e, "caused by: ", e.__cause__)

    def do_start(self, line):
        print("starting watcher with config file: ")
        pass

    def do_stop(self, line):
        print("stopping watcher")
        pass

    def do_exit(self, line):
        print("Exiting sparrow shell")
        return True

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
    SparrowCmd().cmdloop()
