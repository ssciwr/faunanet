import click

from iSparrow import SparrowWatcher, utils


def process_config():
    pass


@click.cli
def cli():
    pass


@cli.command
def set_up():
    pass


@cli.command
def start():
    watcher.start()


@cli.command
def pause():
    watcher.pause()


@cli.command
def stop():
    watcher.stop()


@cli.command
def go_on():
    watcher.go_on()


@cli.command
def clean_up():
    watcher.clean_up()


@cli.command
def run():
    global watcher
    watcher = SparrowWatcher("input", "output", ...)
    watcher.start()
