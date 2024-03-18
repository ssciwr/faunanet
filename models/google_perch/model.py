import sys

sys.path.append("../../src/iSparrow")

from pathlib import Path
import numpy as np
import tensorflow as tf
from birdnetlib.analyzer import AnalyzerConfigurationError
import csv
from src.iSparrow.sparrow_model_base import ModelBase
import src.iSparrow.utils as utils
import pandas as pd


class Model(ModelBase):

    def __init__(self, model_path: str, num_threads: int = 1):
        """
        __init__ Create a new Model instance using the google perch model.

        Args:
            model_path (str): Path to the model file to load from disk
            num_threads (int): The number of threads used for inference. Currently not used for this model.
        """
        labels_path = str(Path(model_path) / "labels.txt")

        super().__init__(
            model_path, labels_path, num_threads
        )  # num_threads doesn't do anything here.

        self.model_path = str(
            Path(model_path) / "saved_model.pb"
        )  # tensorflow wants to add the "saved_model.pb" itself, so we set the member after the superclass cstor

    def load_model(self):
        """
        load_model Read the model from file.

        """
        self.model = tf.saved_model.load(self.model_path)

    def load_labels(self):
        """
        load_labels Read the labels file as a pandas dataframe.
        """
        self.labels = pd.read_csv(
            self.labels_path,
        )

    def predict(self, data: np.array):
        """
        predict Make inference about the bird species for the preprocessed data passed to this function as arguments.

        Args:
            data (list): list of preprocessed data chunks
        """
        # FIXME: this does work programmatically, but gives awful results

        results = self.labels.copy()

        # README: this should be parallelized??
        logits, embeddings = self.model.infer_tf(
            np.array(
                [
                    data,
                ]
            )
        )

        probabilities = tf.nn.softmax(logits).numpy()[0]

        # probabilities = tf.nn.sigmoid(logits).numpy()[0]
        results.loc[:, "probabilities"] = probabilities

        return results

    @classmethod
    def from_cfg(cls, sparrow_folder: str, cfg: dict):
        """
        from_cfg _summary_

        Args:
            cfg (dict): _description_
        """

        cfg["model_path"] = str(
            Path(sparrow_folder) / Path("models") / Path(cfg["model_path"])
        )

        return cls(**cfg)
