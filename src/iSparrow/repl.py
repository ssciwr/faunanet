from iSparrow import SparrowWatcher
from iSparrow import set_up_sparrow, SPARROW_HOME, SPARROW_MODELS
from utils import read_yaml, update_dict_recursive
from pathlib import Path
from platformdirs import user_config_dir
import cmd


def process_line(line: str, keywords: str = None):

    if keywords is not None:
        for keyword in keywords:
            if keyword not in line:
                print(
                    "Invalid input. Expected options structure is --name=<arg> which must contain keywords ",
                    keywords,
                )
                return None

    if "=" not in line:
        print("Invalid input. Expected options structure is --name=<arg>")
        return None

    kwargs = line.split("=")
    args = []

    for i in range(1, len(kwargs), 2):
        args.append(kwargs[i].strip())

    return args


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

        inputs = process_line(
            line,
            [
                "--cfg=",
            ],
        )
        if inputs is None:
            print(
                "Something in the setup command parsing went wrong. Check your passed commands"
            )
            return

        cfg = None

        if len(inputs) > 1:
            print("Invalid input. Expected: set_up --cfg=<config_file>")
            return
        elif len(inputs) == 1:
            cfg = Path(inputs[0]).expanduser().resolve()
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
            raise RuntimeError from e

    def do_start(self, line):
        full_cfg = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "default.yml")

        inputs = process_line(
            line,
            [
                "--cfg=",
            ],
        )

        if self.watcher is None:

            if cfg is not None:
                custom_cfg = read_yaml(cfg)
                update_dict_recursive(full_cfg, custom_cfg)

                input = cfg["Data"]["input"]
            else:
                input = input

            if output is None:
                output = cfg["Data"]["output"]
            else:
                output = output

            try:

                self.watcher = SparrowWatcher(
                    indir=input,
                    outdir=output,
                    model_dir=MODELS,
                    model_name=full_cfg["Analysis"]["model_name"],
                    model_config=full_cfg["Analysis"]["Model"],
                    preprocessor_config=full_cfg["Data"]["Preprocessor"],
                    recording_config=full_cfg["Analysis"]["Recording"],
                    species_predictor_config=full_cfg["Analysis"].get(
                        "SpeciesPredictor", None
                    ),
                    pattern=full_cfg["Analysis"]["pattern"],
                    check_time=full_cfg["Analysis"]["check_time"],
                    delete_recordings=full_cfg["Analysis"]["delete_recordings"],
                )
            except Exception as e:
                click.echo(
                    f"An error occured while trying to start the watcher: {e} caused by {e.__cause__}"
                )
                self.watcher = None

            try:
                self.watcher.start()
            except RuntimeError as e:
                click.echo(
                    f"Something went wrong while trying to start the watcher process: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed.",
                )

        elif self.watcher.is_running:
            click.echo(
                "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters."
            )
        else:
            click.echo(
                "It appears that there is a watcher process that is not running. Trying to start"
            )
            try:
                self.watcher.start()
            except RuntimeError as e:
                click.echo(
                    f"Something went wrong while trying to start the watcher process: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed."
                )

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
