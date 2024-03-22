import pytest
import shutil

from . import make_mock_install
from .fixtures.recording_fixtures import recording_fx
from .fixtures.preprocessor_fixtures import preprocessor_fx, preprocessor_fx_google
from .fixtures.model_fixtures import model_fx


# add a fixture with session scope that emulates the result of a later to-be-implemented-install-routine
@pytest.fixture(scope="session", autouse=True)
def install(request):
    print("Creating iSparrow folders and downloading data... ")
    make_mock_install.install()
    print("Installation finished")

    # remove again after usage
    def teardown():
        shutil.rmtree(str(make_mock_install.HOME))
        shutil.rmtree(str(make_mock_install.DATA))
        shutil.rmtree(str(make_mock_install.OUTPUT))

    request.addfinalizer(teardown)
