import pytest
import shutil
from pathlib import Path

from .fixtures.recording_fixtures import recording_fx

from .fixtures.preprocessor_fixtures import preprocessor_fx

from .fixtures.analyzer_fixtures import analyzer_fx


# add a fixture with session scope that emulates the result of a later to-be-implemented-install-routine
@pytest.fixture(scope="session", autouse=True)
def install(request):
    # README:
    # make a hidden folder 'iSparrow' in the home directory
    # copy the models there
    # copy the content of the example folder into another folder within ~/iSparrow that's called 'data'
    # These locations can later be set once the whole thing runs and has an install routine. then this routine can be removed again

    sparrow_lib_folder = Path(__file__).resolve().parent.parent

    print("lib folder: ", sparrow_lib_folder)

    model_source_folder = sparrow_lib_folder / Path("models")

    sparrow_folder = Path.home() / Path("iSparrow")

    model_folder = sparrow_folder / Path("models")

    data_folder = sparrow_folder / Path("data")

    # make needed folders
    model_folder.mkdir(parents=True, exist_ok=True)

    data_folder.mkdir(parents=True, exist_ok=True)

    for model in ["birdnet_defaults", "birdnet_custom"]:

        # make models folder
        (model_folder / Path(model)).mkdir(parents=True, exist_ok=True)

        for file_to_copy in ["model.tflite", "labels.txt"]:
            shutil.copy(
                str(model_source_folder / Path(model) / Path(file_to_copy)),
                str(model_folder / Path(model)),
            )

    for file_to_copy in (sparrow_lib_folder / Path("tests") / Path("example")).iterdir():
        shutil.copy(
            str(sparrow_lib_folder / Path("tests") / Path("example") / file_to_copy),
            str(data_folder),
        )

    def teardown():
        shutil.rmtree(str(sparrow_folder))

    request.addfinalizer(teardown)
