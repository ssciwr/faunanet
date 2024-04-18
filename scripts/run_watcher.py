from iSparrow import SparrowWatcher 
import time
from pathlib import Path
from datetime import datetime 
from copy import deepcopy 

if __name__ == "__main__":
    preprocessor_cfg = {
                "sample_rate": 48000,
                "overlap": 0.0,
                "sample_secs": 3.0,
                "resample_type": "kaiser_fast",
            }

    model_cfg = {
        "num_threads": 1,
        "sigmoid_sensitivity": 1.0,
        "species_list_file": None,
    }

    recording_cfg = {
        # "date": datetime(year=2024, month=1, day=24),
        # "lat": 42.5,
        # "lon": -76.45,
        "species_presence_threshold": 0.03,
        "min_conf": 0.25,
        "species_predictor": None,
    }

    species_predictor_cfg = {
        "use_cache": True,
        "num_threads": 1,
    }

    custom_preprocessor_cfg = {
        "sample_rate": 48000,
        "overlap": 0.0,
        "sample_secs": 3.0,
        "resample_type": "kaiser_fast",
    }

    custom_model_cfg = {
        "num_threads": 1,
        "sigmoid_sensitivity": 1.0,
        "default_model_path": str(Path.home() / "iSparrow/models/birdnet_default"),
    }

    custom_species_predictor_cfg = {}

    watcher = SparrowWatcher(
        Path.home() / "iSparrow_data",
        Path.home() / "iSparrow_output",
        Path.home()/ "iSparrow" / "models",
        "birdnet_default",
        preprocessor_config=deepcopy(preprocessor_cfg),
        model_config=deepcopy(model_cfg),
        recording_config=deepcopy(recording_cfg),
        # species_predictor_config=deepcopy(species_predictor_cfg),
        delete_recordings="never"
    )

    watcher.start()

    time.sleep(280)

    watcher.change_analyzer(
        "birdnet_custom", 
        preprocessor_config = custom_preprocessor_cfg,
        model_config = custom_model_cfg,
        recording_config = recording_cfg
    )

    time.sleep(280)

    watcher.stop()

    watcher.clean_up()

    print("done")