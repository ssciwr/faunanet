from abc import ABC, abstractmethod
import numpy as np
from pathlib import Path


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
    ):
        self.num_threads = num_threads

        if Path(model_path).exists() is False:
            raise FileNotFoundError(f"No model file at {model_path}")

        if Path(labels_path).exists() is False:
            raise FileNotFoundError(f"No labels file at {labels_path}")

        if species_list_path is not None and Path(species_list_path).exists() is False:
            raise FileNotFoundError(f"No file found at {species_list_path}")

        self.model_path = model_path

        self.labels_path = labels_path

        self.species_list_path = species_list_path

        self.load_model()

        self.load_labels()

        if self.species_list_path is not None:
            self.load_species_list()

    @abstractmethod
    def load_labels(self):
        pass

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def load_species_list(self):
        pass

    @abstractmethod
    def predict(self, data: np.array) -> np.array:
        pass
