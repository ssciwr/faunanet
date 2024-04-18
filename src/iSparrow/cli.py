import click

from iSparrow import SparrowWatcher, utils
import iSparrow.set_up as sus
from appdirs import user_config_dir
from datetime import datetime
from pathlib import Path
from copy import deepcopy

WATCHER = None
RECORDER = None
TRANSMITTER = None
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
    if (
        "date" in config["Analysis"]["Recording"]
        and config["Analysis"]["Recording"]["date"] is not None
    ):
        d = datetime.strptime(config["Analysis"]["Recording"]["date"], "%d-%m-%Y")
        config["Analysis"]["Recording"]["date"] = d

    # set the data needed for running
    watcher_cfg = config["Analysis"]["Watcher"]
    recording_cfg = config["Analysis"]["Recording"]
    preprocessor_cfg = config["Analysis"]["Preprocessor"]
    model_cfg = config["Analysis"]["Model"]

    if "SpeciesPredictor" in config["Analysis"]:
        species_predictor_cfg = config["Analysis"]["SpeciesPredictor"]
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
    ctx.obj = {
        "cfg": cfg,
    }

    ctx.obj["commands"] = {
        "start_watcher": start_watcher,
        "stop_watcher": stop_watcher,
        "change_analyzer": change_analyzer,
        "clean_up": clean_up,
        "show": show,
        "run": run,
        "create_new_watcher": create_new_watcher,
        "delete_watcher": delete_watcher,
        "check_watcher": check_watcher,
    }


@cli.command()
@click.pass_context
def start(ctx):
    """
    start _summary_

    Args:
        ctx (_type_): _description_
    """
    command_map = ctx.obj["commands"]

    # process configuration files into install and one single config
    (
        install,
        watcher_cfg,
        recording_cfg,
        preprocessor_cfg,
        model_cfg,
        species_predictor_cfg,
    ) = process_configs(ctx.obj["cfg"])

    # set folders
    global HOME, DATA, MODELS, OUTPUT, CONFIG
    HOME = Path(install["Directories"]["home"]).expanduser()
    DATA = Path(install["Directories"]["data"]).expanduser()
    MODELS = Path(install["Directories"]["models"]).expanduser()
    OUTPUT = Path(install["Directories"]["output"]).expanduser()
    CONFIG = Path(user_config_dir("iSparrow")) / install["Directories"]["config"]

    # write out configs for recorder and transmitter when they are there

    ctx.obj["watcher_cfg"] = watcher_cfg
    ctx.obj["recording_cfg"] = recording_cfg
    ctx.obj["preprocessor_cfg"] = preprocessor_cfg
    ctx.obj["species_predictor_cfg"] = species_predictor_cfg
    ctx.obj["model_cfg"] = model_cfg

    while True:
        prompt_msg = "What do you want to do? (type exit to exit the program)"
        choice = click.prompt(prompt_msg, type=str)

        if choice in command_map:
            click.echo(f"Executing {choice}...")
            command_map[choice]()
        elif choice == "exit":
            click.echo("Exiting...")
            return
        else:
            click.echo("Invalid choice.")


@cli.command()
@click.option("--cfg", help="custom configuration file", default="")
@click.pass_context
def set_up(ctx, cfg: str):
    """
    set_up _summary_

    _extended_summary_

    Args:
        ctx (_type_): _description_
        cfg (str): _description_

    Raises:
        FileNotFoundError: _description_
    """
    if Path(cfg).expanduser().is_dir() is False:
        raise FileNotFoundError("Given config foler not found")

    click.echo("Starting set up")

    sus.install(Path(cfg).expanduser())

    click.echo("iSparrow set up")


def show():
    """
    show _summary_

    _extended_summary_
    """
    ctx = click.get_current_context()
    click.echo("Available commands")
    click.echo(list(ctx.obj["commands"].keys()))


def run():
    """
    run _summary_

    """

    create_new_watcher()
    start_watcher()


def create_new_watcher():
    """
    create_new_watcher _summary_

    """
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
    """
    check_watcher _summary_
    """
    running = "is" if WATCHER.is_running else "is not"
    click.echo(f"watcher {running} running")

    paused = "is not" if WATCHER.may_do_work.is_set() else "is"
    click.echo(f"watcher is {paused} paused")


def delete_watcher():
    """
    delete_watcher _summary_

    Raises:
        RuntimeError: _description_
    """
    global WATCHER

    if WATCHER is not None and WATCHER.is_running:
        raise RuntimeError("Watcher cannot be deleted while it's running")

    WATCHER = None


def start_watcher():
    """
    start_watcher _summary_

    """
    click.echo("start_watcher")
    WATCHER.start()


def stop_watcher():
    """
    stop_watcher _summary_

    Raises:
        RuntimeError: _description_
    """
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


def change_analyzer():
    global WATCHER

    if WATCHER is None:
        raise RuntimeError("No watcher initialized")

    ctx = click.get_current_context()
    cfg = click.prompt(
        "Please enter the path to the config file defining the new analyzer: "
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

    WATCHER.change_analyzer(
        model_name,
        preprocessor_config=preprocessor_cfg,
        model_config=mcfg,
        recording_config=recording_cfg,
        species_predictor_config=species_predictor_cfg,
    )


def clean_up():
    global WATCHER
    if WATCHER is None:
        raise RuntimeError("No watcher has been initialized, clean_up cannot be run")

    WATCHER.clean_up()
