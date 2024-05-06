from iSparrow import SparrowWatcher
from iSparrow import set_up_sparrow, SPARROW_HOME, SPARROW_MODELS
import click
from platformdirs import user_config_dir
from utils import read_yaml, update_dict_recursive
from pathlib import Path

INPUT = None
OUTPUT = None
WATCHER = None
HOME = None
MODELS = None


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--cfg",
    help="Directory that contains 'install.yml' and 'default.yml' files.",
    default=None,
)
def set_up(cfg: str):
    set_up_sparrow(cfg)
    global HOME, MODELS
    HOME = SPARROW_HOME
    MODELS = SPARROW_MODELS


@cli.command
@click.option(
    "--input",
    help="Directory to read audio files from. Overrides the respective entry in the config file.",
    default=None,
)
@click.option(
    "--output",
    help="Directory to store analyzed data in. Overrides the respective entry in the config file.",
    default=None,
)
@click.option(
    "--cfg",
    help="Path to custom config file. Overrides corresponding entries in the default config.",
    default=None,
)
def start(input: str, output: str, cfg: str):

    global INPUT, OUTPUT, WATCHER, MODELS

    full_cfg = read_yaml(Path(user_config_dir()) / Path("iSparrow") / "default.yml")

    if WATCHER is None:

        if cfg is not None:
            custom_cfg = read_yaml(cfg)
            update_dict_recursive(full_cfg, custom_cfg)

            INPUT = cfg["Data"]["input"]
        else:
            INPUT = input

        if output is None:
            OUTPUT = cfg["Data"]["output"]
        else:
            OUTPUT = output

        try:

            WATCHER = SparrowWatcher(
                indir=INPUT,
                outdir=OUTPUT,
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
            WATCHER = None

        try:
            WATCHER.start()
        except RuntimeError as e:
            click.echo(
                f"Something went wrong while trying to start the watcher process: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed.",
            )

    elif WATCHER.is_running:
        click.echo(
            "The watcher is running. Cannot be started again with different parameters. Try 'change_analyzer' to use different parameters."
        )
    else:
        click.echo(
            "It appears that there is a watcher process that is not running. Trying to start"
        )
        try:
            WATCHER.start()
        except RuntimeError as e:
            click.echo(
                f"Something went wrong while trying to start the watcher process: {e} caused by  {e.__cause__}. A new start attempt can be made when the error has been addressed."
            )


@cli.command()
def stop():
    global WATCHER
    if WATCHER is None:
        click.echo(
            "Cannot stop watcher process. No watcher has been created yet. Run 'start' first."
        )
    elif WATCHER.is_running is False:
        click.echo("Cannot stop watcher process because it is not running.")
    else:
        click.echo("Stopping watcher process.")
        try:
            WATCHER.stop()
            while WATCHER.is_running:
                time.sleep(1)
        except RuntimeError as e:
            click.echo(
                "Something went wrong while trying to stop the watcher process: ",
                e,
                " caused by ",
                e.__cause__,
                ", the process will be killed now and must be manually restarted.",
            )
            if WATCHER.watcher_process is not None and WATCHER.watcher_process.is_alive:
                WATCHER.watcher_process.kill()

        WATCHER = None


@cli.command()
def pause():
    global WATCHER
    if WATCHER is None:
        click.echo(
            "Cannot pause watcher process. No watcher has been created yet. Run 'start' first."
        )
    elif WATCHER.is_running is False:
        click.echo("Cannot pause watcher process because it is not running.")
    else:
        click.echo("Stopping watcher process")
        WATCHER.pause()
        while WATCHER.may_do_work.is_set():
            time.sleep(1)


@cli.command()
def go_on():
    global WATCHER
    if WATCHER is None:
        click.echo(
            "Cannot pause watcher process. No watcher has been created yet. Run 'start' first."
        )
    elif WATCHER.is_running is False:
        click.echo("Cannot continue watcher process because it is not running.")
    elif WATCHER.is_sleeping is False:
        click.echo("Cannot continue the watcher process because it is not asleep.")
    else:
        WATCHER.go_on()


@cli.command()
def restart():
    global WATCHER
    if WATCHER is None:
        click.echo(
            "Cannot restart the watcher because it has not yet been created. Run 'start' first."
        )
    elif WATCHER.is_running is False:
        click.echo("The watcher is not running. Call 'start' first")
    elif WATCHER.is_sleeping:
        click.echo("The watcher is asleep. Continue it first and then restart.")
    else:
        try:
            WATCHER.restart()
        except RuntimeError as e:
            click.echo(
                "An error occured when trying to restart the process: ",
                e,
                " caused by ",
                e.__cause__,
                ". Killing the process now because it may be in an inconsistent state",
            )
            if WATCHER.watcher_process is not None and WATCHER.watcher_process.is_alive:
                WATCHER.watcher_process.kill()

            while WATCHER.watcher_process.is_alive:
                time.sleep(1)


@cli.command()
@click.option(
    "--input",
    help="Directory to read audio files from. Overrides the respective entry in the config file.",
    default=None,
)
@click.option(
    "--output",
    help="Directory to store analyzed data in. Overrides the respective entry in the config file.",
    default=None,
)
@click.option(
    "--cfg",
    help="Path to custom config file. Overrides corresponding entries in the default config.",
    default=None,
)
def change_analyzer(input: str, output: str, cfg: str):

    global INPUT, OUTPUT, WATCHER

    if WATCHER is None:
        click.echo(
            "Watcher has not been created, cannot change analyzer consequently. Run 'start' first."
        )
    elif WATCHER.is_running is False:
        click.echo("Watcher is not running, cannot change analyzer")
    elif WATCHER.is_sleeping is False:
        click.echo(
            "Watcher is sleeping. Continue first before trying to change the analyzer"
        )

    if cfg is None:
        click.echo(
            "When trying to change the analyzer you must give a new config file."
        )

    full_cfg = read_yaml(Path(user_config_dir() / "iSparrow") / "default.yml")
    custom_cfg = read_yaml(cfg)
    update_dict_recursive(full_cfg, custom_cfg)

    if input is not None:
        INPUT = cfg["Data"]["input"]
    else:
        INPUT = input
    if output is not None:
        OUTPUT = cfg["Data"]["output"]
    else:
        OUTPUT = output

    try:
        WATCHER.change_analyzer(
            model_name=full_cfg["Analysis"]["model_name"],
            model_config=full_cfg["Analysis"]["Model"],
            preprocessor_config=full_cfg["Data"]["Preprocessor"],
            recording_config=full_cfg["Analysis"]["Recording"],
            species_predictor_config=full_cfg["Analysis"].get("SpeciesPredictor", None),
            pattern=full_cfg["Analysis"]["pattern"],
            check_time=full_cfg["Analysis"]["check_time"],
            delete_recordings=full_cfg["Analysis"]["delete_recordings"],
        )
    except RuntimeError as e:
        click.echo(
            "An error occured while trying to change the analyzer: ",
            e,
            ", caused by ",
            e.__cause__,
            ". The watcher has been reset to its initial state, but must be restarted by hand",
        )


@cli.command()
def clean_up():
    global WATCHER
    if WATCHER is None:
        click.echo(
            "Cannot run cleanup because there is no active watcher process. Run 'start' first."
        )
    else:
        WATCHER.clean_up()


@cli.command()
@click.option("--attribute", help="Attribute to retrieve from Watcher. ", default=None)
def get_from_watcher(attribute: str):
    global WATCHER
    if attribute is None:
        click.echo("Cannot retrieve attribute 'None'")
    elif WATCHER is None:
        click.echo("No existing Watcher, run 'start' first. ")
    else:
        try:
            attr = str(WATCHER.__getattribute__(attribute))
            click.echo(attr)
        except Exception as e:
            click.echo(
                "Something went wrong while retrieving attribute of Watcher ", attribute
            )


@cli.command()
def status():
    global WATCHER
    if WATCHER is None:
        click.echo("No watcher present")
    elif WATCHER.is_sleeping:
        click.echo("Watcher is sleeping")
    elif WATCHER.is_running:
        click.echo("Watcher is running")


if __name__ == "__main__":
    cli()
