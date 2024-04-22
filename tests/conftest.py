import pytest
import shutil
import multiprocessing

multiprocessing.set_start_method("spawn")
from . import set_up_sparrow_env
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
    set_up_sparrow_env.install(for_tests=True)
    print("Installation finished")

    global HOME, DATA, OUTPUT
    HOME = set_up_sparrow_env.HOME
    DATA = set_up_sparrow_env.DATA
    OUTPUT = set_up_sparrow_env.OUTPUT

    # remove again after usage
    def teardown():
        shutil.rmtree(str(DATA))
        shutil.rmtree(str(OUTPUT))

    request.addfinalizer(teardown)
