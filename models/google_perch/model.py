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

    def __init__(self, model_path: str):
        """
        __init__ Create a new Model instance using the google perch model.

        Args:
            model_path (str): Path to the model file to load from disk
        """
        model_path = Path(model_path) / "model.pb"
        labels_path = Path(model_path) / "labels.txt"

        super().__init__(
            model_path, labels_path, 1
        )  # num_threads doesn't do anything here.

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

    def predict(self, data: list):
        """
        predict Make inference about the bird species for the preprocessed data passed to this function as arguments.

        Args:
            data (list): list of preprocessed data chunks
        """
        final_results = []

        start = 0

        for i, chunk in enumerate(data):
            print(i, "/", len(data))

            results = self.labels.copy()

            # README: this should be parallelized??
            logits, embeddings = self.model.infer_tf(
                np.array(
                    [
                        chunk,
                    ]
                )
            )

            probabilities = tf.nn.softmax(logits).numpy()[0]

            # probabilities = tf.nn.sigmoid(logits).numpy()[0]
            results.loc[:, "probabilities"] = probabilities

            if len(results) > 0:
                results.loc[:, "start_time"] = start

                results.loc[:, "end_time"] = start + 5

                start += 5

                final_results.append(results)

        self.results = pd.concat(final_results)
