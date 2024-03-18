import sys
from pathlib import Path
import numpy as np

from birdnetlib.analyzer import AnalyzerConfigurationError

sys.path.append("../../src/iSparrow")
from src.iSparrow.sparrow_model_base import ModelBase
import src.iSparrow.utils as utils


class Model(ModelBase):
    """
    Model Model class representing the the default birdnet model. Does currently not support custom species list or species prediction based on coordinates.

    """

    def __init__(
        self, model_path: str, num_threads: int = 1, sigmoid_sensitivity: float = 1.0
    ):
        """
        __init__ Create a new model instance that uses birdnet-analyzer models for bird species classification

        Args:
            model_path (str): Path to the location of the model file to be loaded
            num_threads (int, optional): Number of threads used for inference. Defaults to 1.
            sigmoid_sensitivity (float, optional): Parameter of the sigmoid function used to compute probabilities. Defaults to 1.0.

        Raises:
            AnalyzerConfigurationError: The model file 'model.tflite' doesn't exist at the given path.
            AnalyzerConfigurationError: The labels file 'labels.txt' doesn't exist at the given path.
        """

        self.num_threads = num_threads

        self.model_path = str(Path(model_path) / "model.tflite")

        self.labels_path = str(Path(model_path) / "labels.txt")
        self.sensitivity = sigmoid_sensitivity
        self.interpreter = None
        self.input_layer_index = 0
        self.output_layer_index = 0

        # make sure species list paths exists

        # make sure default model is found
        if Path(self.model_path).exists() is False:
            raise AnalyzerConfigurationError(
                f"Error, default model could not be found at provided path {self.model_path}"
            )

        if Path(self.labels_path).exists() is False:
            raise AnalyzerConfigurationError(
                f"Error, default label could not be found at provided path {self.labels_path}"
            )

        self.load_model()
        self.load_labels()

    def load_model(self):
        """
        load_model Override of the base class load model to get the correct paths and make sure that we have multithreading.
        """

        self.interpreter = utils.load_model_from_file_tflite(
            self.model_path, num_threads=self.num_threads
        )

        # Get input and output tensors.
        input_details = self.interpreter.get_input_details()

        output_details = self.interpreter.get_output_details()

        # Get input tensor index
        self.input_layer_index = input_details[0]["index"]

        # Get classification output or feature embeddings as output, depending on presence fo custom classifier
        self.output_layer_index = output_details[0]["index"]

        print("Default model loaded ")

    # README: this overrides the load method of the base class to make sure we use the correct paths
    def load_labels(self) -> None:
        """
        load_labels Load labels for classes from file.
        """
        labels = []
        with open(self.labels_path, "r") as lfile:
            for line in lfile.readlines():
                labels.append(line.replace("\n", ""))
        self.labels = labels
        print("Default labels loaded.")

    def predict(self, sample: np.array) -> np.array:
        """
        predict _summary_

        Args:
            sample (np.array): _description_

        Returns:
            list: _description_
        """

        self.interpreter.resize_tensor_input(
            self.input_layer_index, [len(sample), *sample[0].shape]
        )

        self.interpreter.allocate_tensors()

        # Extract feature embeddings
        self.interpreter.set_tensor(
            self.input_layer_index, np.array(sample, dtype="float32")
        )

        self.interpreter.invoke()

        features = self.interpreter.get_tensor(self.output_layer_index)

        # map to probabilities
        probabilities = self._sigmoid(features, -self.sensitivity)
        return probabilities

    def _sigmoid(self, logits: np.array, sensitivity: float = -1):
        """
        _sigmoid Apply a simple sigmoid to output logits to map to probabilities

        Args:
            logits (np.array): Raw output from a the inference function of the loaded model.
            sensitivity (float, optional): Sigmoid parameter. Defaults to -1.

        Returns:
            np.array: Model output mapped to [0,1] to get interpretable probability
        """
        return 1 / (1.0 + np.exp(sensitivity * np.clip(logits, -15, 15)))

    @classmethod
    def from_cfg(cls, sparrow_folder: str, cfg: dict):

        cfg["model_path"] = str(
            Path(sparrow_folder) / Path("models") / cfg["model_path"]
        )

        print(type(cfg["model_path"]))

        return cls(**cfg)
