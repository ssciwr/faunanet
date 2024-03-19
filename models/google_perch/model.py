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

    def __init__(self, model_path: str, num_threads: int = 1, species_list_file=None):
        """
        __init__ Create a new Model instance using the google perch model.

        Args:
            model_path (str): Path to the model file to load from disk
            num_threads (int): The number of threads used for inference. Currently not used for this model.
        """
        labels_path = str(Path(model_path) / "labels.txt")

        species_list_path = None

        if species_list_file is not None:
            species_list_path = str(Path(model_path) / species_list_file)

        self.class_mask = None  # used later

        super().__init__(
            model_path,
            labels_path,
            num_threads=num_threads,
            species_list_path=species_list_path,
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

    def load_species_list(self):
        """
        load_species_list Produce a mask that only takes into account the relevant species given by the species list file supplied to the constructor.
        """

        print("prepare species list")

        # this is particular to this model here
        labels = self.labels["labels"].to_list()

        relevant_labels = set(
            pd.read_csv(self.species_list_path).loc[:, "primary_label"].unique()
        )

        # make boolean mask for probabilities
        self.class_mask = np.array(
            [1 if label in relevant_labels else 0 for label in labels]
        )

        print("done")

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

        confidence = tf.nn.softmax(logits).numpy()[0]

        # set all the species to zero confidence that are not in the species list provided

        if self.class_mask is not None:
            confidence[self.class_mask == 0] = 0

        results.loc[:, "confidence"] = confidence

        return results

    def _sigmoid(self, logits: np.array, sensitivity: float = -1):
        """
        _sigmoid Apply a simple sigmoid to output logits to map them to probabilities

        Args:
            logits (np.array): Raw output from a the inference function of the loaded model.
            sensitivity (float, optional): Sigmoid parameter. Defaults to -1.

        Returns:
            np.array: Model output mapped to [0,1] to get interpretable probability
        """
        return 1 / (1.0 + np.exp(sensitivity * np.clip(logits, -15, 15)))

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
