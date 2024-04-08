from iSparrow import ModelBase
from iSparrow import PreprocessorBase
from iSparrow import SparrowRecording
from iSparrow import SpeciesPredictorBase
from iSparrow import utils

from pathlib import Path
import pandas as pd
from datetime import datetime
import watchdog as wdg


class SparrowAnalyzer:

    def _watch(self):
        pass

    def _analyze(self, file: str):
        pass

    def _batch_analyze(self, files: list):
        pass

    def _write_results(self):
        pass

    def _download_model(self):
        pass

    def _process_stop_time(self):
        pass

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        model_dir: str,
        model: str = "birdnet_default",
        run_until: datetime = None,
        run_for: int = None,
        write_every: int = 100,
        num_threads: int = 1,
    ):
        pass

    def run(self):
        pass

    def change_model(new_model: str):
        pass

    @classmethod
    def from_cfg(cls, cfg: dict):
        pass
