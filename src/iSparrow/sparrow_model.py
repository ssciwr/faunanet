from abc import ABC, abstractmethod

import numpy as np
import tflite_runtime.interpreter as tflite


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
    def predict(self, data: np.array) -> list:
        pass


class BirdnetModel(ModelBase):
    """
    BirdnetModel _summary_

    Args:
        ModelBase (_type_): _description_
    """

    def __init__(
        self,
        default_model_path,
        default_labels_path,
        classifier_model_path=None,
        classifier_labels_path=None,
        num_threads=1,
    ):
        """
        __init__ _summary_

        Args:
            default_model_path (_type_): _description_
            default_labels_path (_type_): _description_
            classifier_model_path (_type_, optional): _description_. Defaults to None.
            classifier_labels_path (_type_, optional): _description_. Defaults to None.
            num_threads (int, optional): _description_. Defaults to 1.
        """
        pass

    def load_model(self):
        """
        load_model Override of the base class load model to get the correct paths and make sure that we have multithreading.
        """
        self.interpreter = tflite.Interpreter(
            model_path=str(self.default_model_path), num_threads=self.num_threads
        )
        self.interpreter.allocate_tensors()

        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Get input tensor index
        self.input_layer_index = self.input_details[0]["index"]

        # Get classification output or feature embeddings as output, depending on presence fo custom classifier
        if self.use_custom_classifier:
            self.output_layer_index = self.output_details[0]["index"] - 1
        else:
            self.output_layer_index = self.output_details[0]["index"]

        print("Model loaded custom ")

    def load_labels(self):
        """
        load_labels Load labels for classes from file.
        """

        labels_file_path = self.default_labels_path
        if self.classifier_labels_path:
            print("loading custom classifier labels")
            labels_file_path = self.classifier_labels_path
        labels = []
        with open(labels_file_path, "r") as lfile:
            for line in lfile.readlines():
                labels.append(line.replace("\n", ""))
        self.labels = labels
        print("Labels loaded custom.")

    def predict(self, data: np.array) -> list:
        pass
