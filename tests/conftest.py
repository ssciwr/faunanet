import pytest
import shutil
import multiprocessing

from iSparrow import set_up_sparrow, SPARROW_HOME, SPARROW_DATA, SPARROW_OUTPUT
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
    set_up_sparrow(for_tests=True)
    print("Installation finished")

    global HOME, DATA, OUTPUT
    HOME = SPARROW_HOME
    DATA = SPARROW_DATA
    OUTPUT = SPARROW_OUTPUT

    # remove again after usage
    def teardown():
        shutil.rmtree(str(DATA))
        shutil.rmtree(str(OUTPUT))

    request.addfinalizer(teardown)
