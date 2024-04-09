import pytest
import shutil

from . import set_up_sparrow_env
from .fixtures.recording_fixtures import recording_fx
from .fixtures.preprocessor_fixtures import preprocessor_fx, preprocessor_fx_google
from .fixtures.model_fixtures import model_fx
from .fixtures.watcher_fixtures import watch_fx


# add a fixture with session scope that emulates the result of a later to-be-implemented-install-routine
@pytest.fixture(scope="session", autouse=True)
def install(request):
    print("Creating iSparrow folders and downloading data... ")
    set_up_sparrow_env.install()
    print("Installation finished")

    # remove again after usage
    def teardown():
        shutil.rmtree(str(set_up_sparrow_env.HOME))
        shutil.rmtree(str(set_up_sparrow_env.DATA))
        shutil.rmtree(str(set_up_sparrow_env.OUTPUT))

    request.addfinalizer(teardown)
