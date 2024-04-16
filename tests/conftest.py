import pytest
import shutil
from pathlib import Path

from iSparrow import set_up as sus
from .fixtures.recording_fixtures import recording_fx
from .fixtures.preprocessor_fixtures import preprocessor_fx, preprocessor_fx_google
from .fixtures.model_fixtures import model_fx
from .fixtures.watcher_fixtures import watch_fx

HOME = ""
DATA = ""
OUTPUT = ""


# add a fixture with session scope that emulates the result of a later to-be-implemented-install-routine
@pytest.fixture(scope="module", autouse=True)
def install(request):
    print("Creating iSparrow folders and downloading data... ")
    sus.install(Path(__file__).parent / "test_configs")
    print("Installation finished")

    global HOME, DATA, OUTPUT
    HOME = sus.HOME
    DATA = sus.DATA
    OUTPUT = sus.OUTPUT

    # remove again after usage
    def teardown():
        shutil.rmtree(str(DATA))
        shutil.rmtree(str(OUTPUT))

    request.addfinalizer(teardown)


@pytest.fixture()
def folders():
    home = sus.HOME
    data = sus.DATA
    output = sus.OUTPUT

    return home, data, output
