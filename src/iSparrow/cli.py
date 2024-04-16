import click

from iSparrow import SparrowWatcher, utils


def process_config():
    pass


@click.group()
def iSparrow_cli():
    pass


@iSparrow_cli.command()
@click.option("--cfg", help="custom configuration file", default="")
def set_up(cfg: str):
    pass


@iSparrow_cli.command()
def start():
    watcher.start()


@iSparrow_cli.command()
def pause():
    watcher.pause()


@iSparrow_cli.command()
def stop():
    watcher.stop()


@iSparrow_cli.command()
def go_on():
    watcher.go_on()


@iSparrow_cli.command()
def clean_up():
    watcher.clean_up()


@iSparrow_cli.command()
@click.option("--cfg", help="custom configuration file", default="")
def run():
    # make the 
    # make watcher 
    global watcher
    watcher = SparrowWatcher("input", "output", ...)
    watcher.start()


@click.group()
def recorder_cli():
    pass


if __name__ == "__main__": 
    iSparrow_cli()