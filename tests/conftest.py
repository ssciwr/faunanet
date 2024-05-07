import pytest
import shutil
import multiprocessing
from pathlib import Path

import iSparrow.sparrow_setup as sps
from iSparrow.utils import read_yaml

from .fixtures.recording_fixtures import recording_fx
from .fixtures.preprocessor_fixtures import preprocessor_fx, preprocessor_fx_google
from .fixtures.model_fixtures import model_fx
from .fixtures.watcher_fixtures import watch_fx

HOME = ""
DATA = ""
OUTPUT = ""


# add a fixture with session scope that emulates the result of a later to-be-implemented-install-routine
@pytest.fixture(scope="function", autouse=True)
def install(request):
    print("Creating iSparrow folders and downloading data... ")
    sps.set_up_sparrow(Path(__file__).parent / Path("test_configs"))
    print("Installation finished")

    global HOME, DATA, OUTPUT
    HOME = sps.SPARROW_HOME
    DATA = sps.SPARROW_DATA
    OUTPUT = sps.SPARROW_OUTPUT

    # remove again after usage
    def teardown():
        shutil.rmtree(str(DATA))
        shutil.rmtree(str(OUTPUT))

    request.addfinalizer(teardown)
