import iSparrow.sparrow_setup as sps
from pathlib import Path 

def test_setup_simple(): 
    filepath = Path(__file__).parent / "test_configs"

    sps.set_up_sparrow(filepath)

    assert sps.SPARROW_HOME.exists() 
    assert sps.SPARROW_EXAMPLES.exists()
    assert sps.SPARROW_MODELS.exists()
    assert sps.SPARROW_OUTPUT.exists() 
    assert sps.SPARROW_CONFIG.exists() 
    assert sps.SPARROW_CACHE.exists()

    assert (sps.SPARROW_MODELS / "birdnet_default" / "model.tflite").is_file() 
    assert (sps.SPARROW_MODELS / "birdnet_custom" / "model.tflite").is_file() 
    assert (sps.SPARROW_MODELS / "google_perch" / "saved_model.pb").is_file() 
