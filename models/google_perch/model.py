import sys

sys.path.append("../../src/iSparrow")

from pathlib import Path
import numpy as np
import tensorflow as tf
from birdnetlib.analyzer import AnalyzerConfigurationError

from src.iSparrow.sparrow_model_base import ModelBase
import src.iSparrow.utils as utils


class Model(ModelBase):

    def __init__(self, model_path: str, num_threads: int):
        model_path = Path(model_path) / "model.pb"
        labels_path = Path(model_path) / "labels.txt"

        super().__init__(model_path, labels_path, num_threads)

    def load_model(self):
        # README: set tensorflow parallelism. this is tentative and needs to be tested on a per model basis
        tf.config.threading.set_inter_op_parallelism_threads(self.num_threads)
        tf.config.threading.set_intra_op_parallelism_threads(self.num_threads)
        self.model = tf.saved_model.load(self.model_path)

    def load_labels(self):
        pass

    def predict(self):
        pass

    def __del__(self):
        # reset number of threads so future model loadings don't have to inherit it
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.threading.set_intra_op_parallelism_threads(1)
