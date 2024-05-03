from . import watcher_cli
from .utils import read_yaml
import subprocess
import click
from . import setup as stp


@click.group()
def cli():
    pass


@cli.command()
@cli.option("--cfg", help="Configuration file for installation", default=None)
def set_up(cfg: str):

    if cfg is None:
        click.echo("Set up must be called with a configuration file.")

    cfg = read_yaml(cfg)

    stp.setup(cfg)


@watcher_cli.command()
def sparrow_info():
    try:
        install_cfg = read_yaml(user_config_dir / "install.yml")
        click.echo("installation: ", install.cfg)
    except Exception as e:
        click.echo("Could not sucessfully retrieve install config: ", e)

    try:
        default_cfg = read_yml(user_config_dir / "default.yml")
        click.echo(default_cfg)
    except Exception as e:
        click.echo("Could not successfully retrieve default config: ", e)
