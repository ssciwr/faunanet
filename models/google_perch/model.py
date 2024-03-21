import sys

sys.path.append("../../src/iSparrow")

from pathlib import Path
import numpy as np
import tensorflow as tf
from birdnetlib.analyzer import AnalyzerConfigurationError
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

        model_path = str(Path(model_path) / "saved_model.pb")

        species_list_path = None

        if species_list_file is not None:
            species_list_path = str(Path(model_path) / species_list_file)

        self.class_mask = None  # used later

        super().__init__(
            "google_perch_model",
            model_path,
            labels_path,
            num_threads=num_threads,
            species_list_path=species_list_path,
            # sensitivity kwarg doesn't exist here
        )  # num_threads doesn't do anything here.

    # tensorflow wants to add the "saved_model.pb" itself, so we set the member after the superclass cstor

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
            data (np.array): list of preprocessed data chunks
        Returns:
            list: List of (label, inferred_probability)
        """

        results = self.labels.copy()

        # README: this should be parallelized??
        logits, embeddings = self.model.infer_tf(
            np.array(
                [
                    data,
                ]
            )
        )

        results = tf.nn.softmax(logits).numpy()
        return results

    @classmethod
    def from_cfg(cls, sparrow_folder: str, cfg: dict):
        """
        from_cfg Create a new instance from a dictionary containing keyword arguments. Usually loaded from a config file.

        Args:
            sparrow_dir (str): Installation directory of the Sparrow package
            cfg (dict): Dictionary containing the keyword arguments

        Returns:
            Model: New model instance created with the supplied kwargs.
        """

        cfg["model_path"] = str(
            Path(sparrow_folder) / Path("models") / Path(cfg["model_path"])
        )

        return cls(**cfg)
