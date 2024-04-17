import click

from iSparrow import SparrowWatcher, utils
import iSparrow.set_up as sus
from appdirs import user_config_dir
from datetime import datetime
from pathlib import Path
import shutil

watcher = None

def process_config(custom_cfg: str):

    newest_install = get_newest_install()

    default = utils.read_yaml(Path(newest_install)/ "default.yml") 
    custom = utils.read_yml(custom_cfg)

    utils.update_dict_recursive(default, custom)

    return default["Analysis"]["Watcher"], default["Analysis"]["Model"], default["Analysis"]["Preprocessor"], default["Analysis"]["Recording"], default["Analysis"]["SpeciesPredictor"]


def get_install_list():
    if (Path(user_config_dir("iSparrow")) / Path("installations")).is_dir() is False:
        raise FileNotFoundError(
            "The standard iSparrow config folder does not exist. Has iSparrow been set up?"
        )

    def check_install(folder): 
        install = utils.read_yaml(folder/ "install.yml")
    
        if Path(install["Directories"]["input"]).expanduser().is_dir() is False or 
        Path(install["Directories"]["output"]).expanduser().is_dir() is False: 
            shutil.rmtree(str(Path(folder)))  # delete broken installs
            return False
        else: 
            return True

    return [
        folder
        for folder in (
            Path(user_config_dir("iSparrow")) / Path("installations")
        ).iterdir()
        if folder.is_dir() and check_install(folder)
    ]


def get_newest_install():
    sorted_folders = sorted(
        get_install_list(), key=lambda folder: folder.stat().st_mtime, reverse=True
    )

    if len(sorted_folders) == 0:
        raise RuntimeError(
            "No installations found in",
            Path(user_config_dir("iSparrow")) / Path("installations"),
            "This should no happen in a normal installation of iSparrow",
        )
    else:
        return sorted_folders[0]


@click.group()
def iSparrow_cli():
    pass


@iSparrow_cli.command()
@click.option("--cfg", help="custom configuration file", default="")
def set_up(cfg: str):
    sus.install(cfg)

    date = datetime.now().strftime("%y%m%d_%H%M%S")

    lookup_dir = (
        user_config_dir("iSparrow") / Path("installations") / f"install_{date}"
    ).mkdir(parents=True, exist_ok=True)

    shutil.copy(str(Path(cfg) / "install.yml"), lookup_dir)
    shutil.copy(str(Path(cfg) / "default.yml"), lookup_dir)


@iSparrow_cli.command()
def start_watcher():
    global watcher
    if watcher is None:
        raise RuntimeError(
            "Watcher does not exist yet. Please create one first with 'iSparrow create --config=/path/to/optional/custom/config"
        )
    watcher.start()


@iSparrow_cli.command()
def pause_watcher():
    global watcher
    if watcher is None:
        raise RuntimeError(
            "Watcher does not exist yet. Please create one first with 'iSparrow create --config=/path/to/optional/custom/config"
        )
    watcher.pause()


@iSparrow_cli.command()
def stop_watcher():
    global watcher
    if watcher is None:
        raise RuntimeError(
            "Watcher does not exist yet. Please create one first with 'iSparrow create --config=/path/to/optional/custom/config"
        )
    watcher.stop()


@iSparrow_cli.command()
def continue_watcher():
    global watcher
    if watcher is None:
        raise RuntimeError(
            "Watcher does not exist yet. Please create one first with 'iSparrow create --config=/path/to/optional/custom/config"
        )
    watcher.go_on()


@iSparrow_cli.command()
def clean_up():
    global watcher
    if watcher is None:
        raise RuntimeError(
            "Watcher does not exist yet. Please create one first with 'iSparrow create --config=/path/to/optional/custom/config"
        )
    watcher.clean_up()


@iSparrow_cli.command()
@click.option(
    "--model",
    help="Name of the model to be loaded. must be present in the watcher's model folder and a watcher must be running.",
)
@click.option(
    "--cfg",
    help="Name of the model to be loaded. must be present in the watcher's model folder and a watcher must be running.",
    default="",
)
def change_analyzer(model_name: str, cfg: str):
    global watcher

    _, model_cfg, preprocessor_cfg, recording_cfg, species_predictor_cfg = (
        process_config(cfg)
    )
    watcher.change_analyzer(
        model_name,
        preprocessor_config=preprocessor_cfg,
        model_config=model_cfg,
        recording_config=recording_cfg,
        species_predictor_config=species_predictor_cfg,
    )


@iSparrow_cli.command()
@click.option("--cfg", help="custom configuration file", default="")
def create_watcher(cfg: str):

    # make watcher
    watcher_cfg, model_cfg, preprocessor_cfg, recording_cfg, species_predictor_cfg = (
        process_config(cfg)
    )
    input_dir = watcher_cfg["input"]
    output_dir = watcher_cfg["output"]
    model_dir = watcher_cfg["model_dir"]
    model_name = watcher_cfg["model_name"]

    del watcher_cfg["input"]
    del watcher_cfg["output"]
    del watcher_cfg["model_dir"]
    del watcher_cfg["model_name"]

    global watcher
    watcher = SparrowWatcher(
        input_dir,
        output_dir,
        model_dir,
        model_name,
        preprocessor_config=preprocessor_cfg,
        model_config=model_cfg,
        recording_config=recording_cfg,
        species_predictor_config=species_predictor_cfg,
    )


@iSparrow_cli.command()
def status():
    global watcher
    click.echo(f"watcher is {'running' if watcher.is_running else 'not running'}")


@iSparrow_cli.command()
def batch_times():
    global watcher
    click.echo(watcher.creation_time_first_analyzed)
    click.echo(watcher.creation_time_last_analyzed)


@iSparrow_cli.command()
def folders():
    global watcher
    click.echo("input directory: ", watcher.input_directory)
    click.echo("output directory: ", watcher.output_directory)
    click.echo("model directory: ", watcher.model_dir)
    click.echo("model name: ", watcher.model_name)


@iSparrow_cli.command()
@click.option("--cfg", help="custom configuration file", default="")
def run(cfg: str = None):

    global watcher
    create_watcher(cfg)
    watcher.start()


if __name__ == "__main__":
    iSparrow_cli()
