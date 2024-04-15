from iSparrow import SparrowWatcher, utils
from pathlib import Path
from copy import deepcopy
import time

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
        "species_presence_threshold": 0.03,
        "min_conf": 0.25,
        "species_predictor": None,
    }

    species_predictor_cfg = {
        "use_cache": True,
        "num_threads": 1,
    }

    cfg_path = Path(__file__).resolve().parent.parent.parent / "config"

    cfg = utils.read_yaml(cfg_path / Path("install_cfg.yml"))
    watcher = SparrowWatcher(
        Path(cfg["Directories"]["data"]).expanduser(),
        Path(cfg["Directories"]["output"]).expanduser(),
        Path(cfg["Directories"]["models"]).expanduser(),
        "birdnet_default",
        preprocessor_config=preprocessor_cfg,
        model_config=model_cfg,
        recording_config=deepcopy(recording_cfg),
        species_predictor_config=species_predictor_cfg,
    )

    watcher.start()

    while True:
        try:
            time.sleep(5)

        except KeyboardInterrupt:
            print("stopping watcher")
            watcher.stop()
