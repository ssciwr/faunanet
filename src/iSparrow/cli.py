import click

from iSparrow import SparrowWatcher, utils
import iSparrow.set_up as sus
from appdirs import user_config_dir
from datetime import datetime
from pathlib import Path
import tempfile
import yaml
from copy import deepcopy
import shutil
import time

WATCHER = None
HOME = None
DATA = None
MODELS = None
OUTPUT = None
CONFIG = None


def process_configs(cfg: str):
    """
    process_configs _summary_

    Args:
        cfg (str): _description_

    Raises:
        FileNotFoundError: _description_
        FileNotFoundError: _description_
        FileNotFoundError: _description_
        FileNotFoundError: _description_

    Returns:
        _type_: _description_
    """
    if cfg is not None:
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

    config = utils.read_yaml(Path(user_config_dir("iSparrow")) / "default.yml")

    install = utils.read_yaml(Path(user_config_dir("iSparrow")) / "install.yml")

    for name in ["home", "data", "output", "models"]:
        if Path(install["Directories"][name]).expanduser().is_dir() is False:
            raise FileNotFoundError(
                f"Folder {name} not found, has iSparrow been set up?"
            )

    utils.update_dict_recursive(config, user_config)

    # process recording config

    if "date" in config["Analysis"]["Recording"]:
        d = datetime.strptime(config["Analysis"]["Recording"]["date"], "%d-%m-%Y")
        config["Analysis"]["Recording"]["date"] = d

    # set the data needed for running
    watcher_cfg = cfg["Analysis"]["Watcher"]
    recording_cfg = cfg["Analysis"]["Recording"]
    preprocessor_cfg = cfg["Analysis"]["Preprocessor"]
    model_cfg = cfg["Analysis"]["Model"]

    if "SpeciesPredictor" in cfg["Analysis"]:
        species_predictor_cfg = cfg["Analysis"]["SpeciesPredictor"]
    else:
        species_predictor_cfg = None

    return (
        install,
        watcher_cfg,
        recording_cfg,
        preprocessor_cfg,
        model_cfg,
        species_predictor_cfg,
    )


@click.group()
@click.option(
    "--cfg",
    help="path to the configuration yaml-file that specifies all necessary parameters",
    default=None,
)
@click.option(
    "--recorder",
    help="name of a command/app accessible through a terminal that is used to record audio data. If it accepts a yaml-file for configuration itself as first command line argument, can be configured with the passed config file by supplying a node named like the recorder command with all necessary parameters.",
    default=None,
)
@click.option(
    "--transmitter",
    help="name of a command/app accessible through a terminal that is used to record audio data. If it accepts a yaml-file for configuration itself as first command line argument, can be configured with the passed config file by supplying a node named like the recorder command with all necessary parameters.",
    default=None,
)
@click.pass_context
def cli(ctx, cfg: str, recorder: str, transmitter: str):
    """
    cli _summary_

    _extended_summary_

    Args:
        ctx (_type_): _description_
        cfg (str): _description_
        recorder (str): _description_
        transmitter (str): _description_
    """

    # process configuration files into install and one single config
    (
        install,
        watcher_cfg,
        recording_cfg,
        preprocessor_cfg,
        model_cfg,
        species_predictor_cfg,
    ) = process_configs(cfg)

    # set folders
    global HOME, DATA, MODELS, OUTPUT, CONFIG
    HOME = Path(install["Directories"]["home"]).expanduser()
    DATA = Path(install["Directories"]["data"]).expanduser()
    MODELS = Path(install["Directories"]["models"]).expanduser()
    OUTPUT = Path(install["Directories"]["output"]).expanduser()
    CONFIG = Path(user_config_dir("iSparrow")) / install["Directories"]["config"]

    # write out configs for recorder and transmitter when they are there
    recorder_cfg = {}
    transmitter_cfg = {}
    tempdir = str(tempfile.TemporaryDirectory())

    if recorder in cfg:
        recorder_cfg = cfg[recorder]
        # write to temp dir and pass to the command line of the recorder later
        with open(Path(tempdir) / "recorder.yml") as f:
            yaml.safe_dump(recorder_cfg, f)

    if transmitter in cfg:
        transmitter_cfg = cfg[transmitter]
        with open(Path(tempdir) / "transmitter.yml") as f:
            yaml.safe_dump(transmitter_cfg, f)

        # write to temp dir and pass to the command line of the transmitter later

    ctx.obj = {
        "cfg": cfg,
        "recorder": recorder,
        "transmitter": transmitter,
        "watcher_cfg": watcher_cfg,
        "recording_cfg": recording_cfg,
        "preprocessor_cfg": preprocessor_cfg,
        "transmitter_cfg": transmitter_cfg,
        "species_predictor_cfg": species_predictor_cfg,
        "recorder_cfg": recorder_cfg,
        "model_cfg": model_cfg,
        "tmp_dir": tempdir,
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
        "show": show,
        "run": run,
        "create_new_watcher": create_new_watcher,
        "delete_watcher": delete_watcher,
        "check_watcher": check_watcher,
    }


@cli.command()
@click.pass_context
def start(ctx):
    command_map = ctx.obj["commands"]
    while True:
        prompt_msg = "What do you want to do? (type exit to exit the program): "
        choice = click.prompt(prompt_msg, type=str)

        if choice in command_map:
            click.echo(f"Executing {choice}...")
            command_map[choice]()
        elif choice == "exit":
            click.echo("Exiting...")
            exit()
            return
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

    click.echo("iSparrow set up")


def show():
    ctx = click.get_current_context()
    click.echo("Available commands")
    click.echo(list(ctx.obj["commands"].keys()))


def run():
    ctx = click.get_current_context()
    if "recorder" in ctx.obj:
        start_recorder()

    if "transmitter" in ctx.obj:
        start_transmitter()

    create_new_watcher()
    start_watcher()


def create_new_watcher():
    ctx = click.get_current_context()
    mcfg = deepcopy(ctx.obj["model_cfg"])
    wcfg = deepcopy(ctx.obj["watcher_cfg"])

    model_name = mcfg["model_name"]
    del mcfg["model_name"]
    del wcfg["input"]
    del wcfg["output"]

    global WATCHER

    WATCHER = SparrowWatcher(
        DATA,
        OUTPUT,
        MODELS,
        model_name,
        **wcfg,
        recording_config=ctx.obj["recording_cfg"],
        model_config=mcfg,
        preprocessor_config=ctx.obj["preprocessor_cfg"],
        species_predictor_config=ctx.obj["species_predictor_cfg"],
    )


def check_watcher():
    status = "yes" if WATCHER.is_running else "no"
    click.echo(f"watcher is running? {status}")


def delete_watcher():
    global WATCHER

    if WATCHER is not None and WATCHER.is_running:
        raise RuntimeError("Watcher cannot be deleted while it's running")

    WATCHER = None


def start_watcher():
    click.echo("start_watcher")
    WATCHER.start()


def start_recorder():
    ctx = click.get_current_context()

    click.echo("start_recorder")


def start_transmitter():

    raise NotImplementedError("Transmitter control is not yet implemented")


def stop_watcher():
    click.echo("stopping watcher (will forcefully terminate after 30s)")

    global WATCHER

    if WATCHER is None:
        raise RuntimeError(
            "Cannot stop watcher because it has been stopped before or has not been started yet"
        )
    else:
        click.echo(
            "Warning: if the watcher is watching a directory which has no new data coming in, it will not terminate. You have to use a keyboard interrupt in that case."
        )
        if WATCHER.is_running:
            WATCHER.stop()


def stop_recorder():
    ctx = click.get_current_context()

    click.echo("stop_recorder")


def stop_transmitter():
    ctx = click.get_current_context()

    click.echo("stop_transmitter")


def change_analyzer():
    ctx = click.get_current_context()
    cfg = click.prompt(
        "Please enter the path to the config file defining the new analyzer"
    )

    # process configuration files into install and one single config
    (
        _,
        _,
        recording_cfg,
        preprocessor_cfg,
        model_cfg,
        species_predictor_cfg,
    ) = process_configs(cfg)

    ctx.obj = {
        "cfg": cfg,
        "recording_cfg": recording_cfg,
        "preprocessor_cfg": preprocessor_cfg,
        "species_predictor_cfg": species_predictor_cfg,
        "model_cfg": model_cfg,
    }

    mcfg = deepcopy(ctx.obj["model_cfg"])

    model_name = mcfg["model_name"]
    del mcfg["model_name"]

    global WATCHER
    WATCHER.change_analyzer(
        model_name,
        preprocessor_config=preprocessor_cfg,
        model_config=mcfg,
        recording_config=recording_cfg,
        species_predictor_config=species_predictor_cfg,
    )


def show_results():
    if WATCHER is None:
        raise RuntimeError("No watcher has been initialized, cannot show result")

    files = list(Path(WATCHER.output_directory).iterdir())
    files = sorted(files, key=lambda f: f.stat().st_ctime)

    click.echo("The first 10 files in the current results folder are: ")
    click.echo(files[0:10])
    click.echo("The last 10 files in the current results folder are: ")
    click.echo(files[-10:])


def show_data():
    ctx = click.get_current_context()

    click.echo("show_data")


def clean_up():
    ctx = click.get_current_context()

    click.echo("clean_up")


def detach():
    ctx = click.get_current_context()

    click.echo("detach")


def exit():
    ctx = click.get_current_context()

    for name in [
        Path(ctx.obj["tmp_dir"]) / "recorder.yml",
        Path(ctx.obj["tmp_dir"]) / "transmitter.yml",
    ]:
        if name.is_file():
            name.unlink()


if __name__ == "__main__":
    cli()
