from abc import ABC, abstractmethod

import numpy as np


class ModelBase(ABC):
    """
    ModelBase _summary_

    Args:
        ABC (_type_): _description_
    """

    @abstractmethod
    def load_labels(self):
        pass

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def predict(self, data: np.array) -> np.array:
        pass
