from abc import ABC, abstractmethod
import numpy as np
from pathlib import Path

from . import utils


class ModelBase(ABC):
    """
    ModelBase _summary_

    Args:
        ABC (_type_): _description_
    """

    def __init__(
        self,
        model_path: str,
        labels_path: str,
        num_threads: int = 1,
        species_list_path: str = None,
        sensitivity: float = 1.0,
    ):
        self.num_threads = num_threads

        if utils.is_url(model_path) is False:
            if Path(model_path).exists() is False:
                raise FileNotFoundError(f"No model file at {model_path}")

            if Path(labels_path).exists() is False:
                raise FileNotFoundError(f"No labels file at {labels_path}")

        if species_list_path is not None and Path(species_list_path).exists() is False:
            raise FileNotFoundError(f"No file found at {species_list_path}")

        self.model_path = model_path

        self.labels_path = labels_path

        self.species_list_path = species_list_path

        self.sensitivity = sensitivity

        self.load_model()

        self.load_labels()

        if self.species_list_path is not None:
            self.load_species_list()

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

    def load_labels(self):
        """
        load_labels Read the labels file as a pandas dataframe.
        """
        labels = []
        with open(self.labels_path, "r") as lfile:
            for line in lfile.readlines():
                labels.append(line.replace("\n", ""))
        self.labels = labels
        print("Labels loaded.")

    def load_model(self):
        """
        load_model Load the model to be used for classifying.

        Raises:
            ValueError: When the path to a local model file does not work
            ValueError: When a given url does not refer to a huggingface hub model
        """
        model_loaders = {
            "model.tflite": utils.load_model_from_file_tflite,
            "saved_model.pb": utils.load_model_from_file_pb,
            "model.pt": utils.load_model_from_file_torch,
        }

        # get the model file
        model_filename = str(Path(self.model_path).name)

        # load model locally
        if utils.is_url(self.model_path) is False:

            if model_filename not in model_loaders:
                raise ValueError(f"Model filename unknown: {model_filename}")

            self.model = model_loaders[model_filename](
                self.model_path, self.num_threads
            )
        else:
            if "huggingface" in self.model_path:
                self.model = utils.load_model_from_huggingfacehub(self.model_path)
            else:
                raise ValueError(
                    "Error, url to load model cannot be handled - does it use hugginface? "
                )

    @abstractmethod
    def load_species_list(self):
        pass

    @abstractmethod
    def predict(self, data: np.array) -> np.array:
        pass
