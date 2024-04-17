import click

from iSparrow import SparrowWatcher, utils
import iSparrow.set_up as sus
from appdirs import user_config_dir
from datetime import datetime
from pathlib import Path
import shutil
import threading

WATCHER = None
HOME = None
DATA = None
MODELS = None
OUTPUT = None
CONFIG = None


@click.group()
@click.option(
    "--cfg",
    help="path to the configuration yaml-file that specifies all necessary parameters",
    default="None",
)
@click.option(
    "--recorder",
    help="name of a command/app accessible through a terminal that is used to record audio data. If it accepts a yaml-file for configuration itself, can be configured with the passed config file by supplying a node named like the recorder command with all necessary parameters.",
    default="None",
)
@click.option(
    "--transmitter",
    help="name of a command/app accessible through a terminal that is used to record audio data. If it accepts a yaml-file for configuration itself, can be configured with the passed config file by supplying a node named like the recorder command with all necessary parameters.",
    default="None",
)
@click.pass_context
def cli(ctx, cfg: str, recorder: str, transmitter: str):
    if cfg is None:
        if Path(cfg).expanduser().is_file() is False:
            raise FileNotFoundError("Given config file not found")
        else:
            user_config = utils.read_yaml(cfg)
    else:
        user_config = {}

    if Path(Path(user_config_dir("iSparrow")) / "default.yml").is_file() is False:
        raise FileNotFoundError(
            "Default config file not found. Has iSparrow been set up? "
        )

    if Path(Path(user_config_dir("iSparrow")) / "install.yml").is_file() is False:
        raise FileNotFoundError(
            "Install config file not found. Has iSparrow been set up? "
        )

    cfg = utils.read_yaml(Path(user_config_dir("iSparrow")) / "default.yml")

    install = utils.read_yaml(Path(user_config_dir("iSparrow")) / "install.yml")

    for name in ["home", "data", "output", "models"]:
        if Path(install["Directories"][name]).expanduser().is_dir() is False:
            raise FileNotFoundError(
                f"Folder {name} not found, has iSparrow been set up?"
            )

    utils.update_dict_recursive(cfg, user_config)

    watcher_cfg = cfg["Analysis"]["Watcher"]
    recording_cfg = cfg["Analysis"]["Recording"]
    preprocessor_cfg = cfg["Analysis"]["Preprocessor"]
    model_cfg = cfg["Analysis"]["Model"]

    recorder_cfg = {}
    transmitter_cfg = {}
    if recorder in cfg:
        recorder_cfg = cfg[recorder]

    if transmitter in cfg:
        transmitter_cfg = cfg[transmitter]

    ctx.obj = {
        "cfg": cfg,
        "recorder": recorder,
        "transmitter": transmitter,
        "watcher_cfg": watcher_cfg,
        "recording_cfg": recording_cfg,
        "preprocessor_cfg": preprocessor_cfg,
        "transmitter_cfg": transmitter_cfg,
        "recorder_cfg": recorder_cfg,
        "model_cfg": model_cfg,
    }

    ctx.obj["commands"] = {
        "start_watcher": start_watcher,
        "start_recorder": start_recorder,
        "start_transmitter": start_transmitter,
        "stop_watcher": stop_watcher,
        "stop_recorder": stop_recorder,
        "stop_transmitter": stop_transmitter,
        "change_analyzer": change_analyzer,
        "show_result": show_results,
        "show_data": show_data,
        "clean_up": clean_up,
        "detach": detach,
    }


@cli.result_callback()
def process_commands(processors, **kwargs):
    if not processors:
        ctx = click.get_current_context()
        ctx.invoke(prompt)


@cli.command()
@click.pass_context
def prompt(ctx):
    command_map = ctx.obj["commands"]
    while True:
        prompt_msg = "What do you want to do? (type 'exit' to leave): "
        choice = click.prompt(prompt_msg, type=str)
        if choice == "exit":
            click.echo("Exiting...")
            return
        chosen_command = command_map.get(choice)
        if chosen_command:
            click.echo(f"Executing {choice}...")
            chosen_command()
        else:
            click.echo("Invalid choice.")


@cli.command()
@click.option("--cfg", help="custom configuration file", default="")
@click.pass_context
def set_up(ctx, cfg: str):

    if Path(cfg).expanduser().is_dir() is False:
        raise FileNotFoundError("Given config foler not found")

    click.echo("Starting set up")

    sus.install(Path(cfg).expanduser())

    global HOME, DATA, MODELS, OUTPUT, EXAMPLES, CONFIG

    HOME = sus.HOME
    DATA = sus.DATA
    MODELS = sus.MODELS
    OUTPUT = sus.OUTPUT
    EXAMPLES = sus.EXAMPLES
    CONFIG = sus.CONFIG

    click.echo("iSparrow set up")

    ctx.obj = {}
    ctx.obj["commands"] = {
        "start_watcher": start_watcher,
        "start_recorder": start_recorder,
        "start_transmitter": start_transmitter,
        "stop_watcher": stop_watcher,
        "stop_recorder": stop_recorder,
        "stop_transmitter": stop_transmitter,
        "change_analyzer": change_analyzer,
        "show_result": show_results,
        "show_data": show_data,
        "clean_up": clean_up,
        "detach": detach,
    }


@cli.command()
def start_watcher():

    print("start_watcher")


@cli.command()
def start_recorder():

    print("start_recorder")


@cli.command()
def start_transmitter():

    print("start_transmitter")


@cli.command()
def stop_watcher():

    print("stop_watcher")


@cli.command()
def stop_recorder():

    print("stop_recorder")


@cli.command()
def stop_transmitter():

    print("stop_transmitter")


@cli.command()
def change_analyzer():

    print("change_analyzer")


@cli.command()
def show_results():

    print("show_results")


@cli.command()
def show_data():

    print("show_data")


@cli.command()
def clean_up():

    print("clean_up")


@cli.command()
def detach():

    print("detach")


if __name__ == "__main__":
    cli()
