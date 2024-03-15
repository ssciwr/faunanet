from pathlib import Path
import numpy as np
import utils

from birdnetlib.analyzer import AnalyzerConfigurationError
from sparrow_model_base import ModelBase


class BirdnetDefaultModel(ModelBase):
    """
    BirdnetModel _summary_

    Args:
        ModelBase (_type_): _description_
    """

    def __init__(
        self,
        model_path,
        labels_path,
        num_threads=1,
    ):
        """
        __init__ Create a new model instance that uses birdnet-analyzer models for bird species classification

        Args:
            model_path (_type_): _description_
            labels_path (_type_): _description_
            classifier_model_path (_type_, optional): _description_. Defaults to None.
            classifier_labels_path (_type_, optional): _description_. Defaults to None.
            num_threads (int, optional): _description_. Defaults to 1.
        """

        self.num_threads = num_threads

        self.model_path = model_path
        self.labels_path = labels_path

        self.interpreter = None
        self.input_layer_index = 0
        self.output_layer_index = 0

        # make sure species list paths exists

        # make sure default model is found
        if Path(model_path).exists() is False:
            raise AnalyzerConfigurationError(
                "Error, default model could not be found at provided path"
            )

        if Path(labels_path).exists() is False:
            raise AnalyzerConfigurationError(
                "Error, default label could not be found at provided path"
            )

        self.load_model()
        self.load_labels()

    def load_model(self):
        """
        load_model Override of the base class load model to get the correct paths and make sure that we have multithreading.
        """

        utils.load_model_from_file_tflite(self.model_path, num_threads=self.num_threads)

        # Get input and output tensors.
        input_details = self.interpreter.get_input_details()

        output_details = self.interpreter.get_output_details()

        # Get input tensor index
        self.input_layer_index = input_details[0]["index"]

        # Get classification output or feature embeddings as output, depending on presence fo custom classifier
        if self.use_custom_classifier:
            self.output_layer_index = output_details[0]["index"] - 1
        else:
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

        return features

    @classmethod
    def from_config(cls, cfg: dict):
        return cls(**cfg)
