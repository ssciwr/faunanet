import sys
from pathlib import Path
import numpy as np

from birdnetlib.analyzer import AnalyzerConfigurationError

sys.path.append("../../src/iSparrow")
from src.iSparrow.sparrow_model_base import ModelBase
import src.iSparrow.utils as utils


class Model(ModelBase):

    def _check_classifier_path_integrity(
        self, classifier_model_path: str, classifier_labels_path: str
    ):
        """checks if custom classifier/labels are both given if one is present and the files they point to exist"""

        if (classifier_model_path is not None and classifier_labels_path is None) or (
            classifier_model_path is None and classifier_labels_path is not None
        ):
            raise AnalyzerConfigurationError(
                "Model and label file paths must be specified to use a custom classifier"
            )

        if (
            classifier_model_path is not None
            and Path(classifier_model_path).exists() is False
        ):
            raise AnalyzerConfigurationError(
                f"Custom classifier model could not be found at the provided path {classifier_model_path}"
            )

        if (
            classifier_model_path is not None
            and Path(classifier_labels_path).exists() is False
        ):
            raise AnalyzerConfigurationError(
                f"Custom classifier labels could not be found at the provided path {classifier_labels_path}"
            )

    #
    def __init__(
        self,
        default_model_path: str = None,
        classifier_model_path: str = None,
        custom_species_list_path: str = None,
        custom_species_list: list = None,
        sigmoid_sensitivity: float = 1.0,
        num_threads: int = 1,
    ):
        """
        __init__ _summary_

        _extended_summary_

        Args:
            default_model_path (_type_, optional): _description_. Defaults to None.
            classifier_model_path (_type_, optional): _description_. Defaults to None.
            custom_species_list_path (_type_, optional): _description_. Defaults to None.
            custom_species_list (_type_, optional): _description_. Defaults to None.
            num_threads (int, optional): _description_. Defaults to 1.
        """
        self.default_model_path = str(Path(default_model_path) / "model.tflite")
        self.default_labels_path = str(Path(default_model_path) / "labels.txt")

        self.classifier_model_path = str(Path(classifier_model_path) / "model.tflite")
        self.classifier_labels_path = str(Path(classifier_model_path) / "labels.txt")

        self.sensitivity = sigmoid_sensitivity
        
        # check custom classifier paths through function due to higher complexity
        self._check_classifier_path_integrity(
            self.classifier_model_path, self.classifier_labels_path
        )
        # need to call this custom because the super class has no prefix..
        self.custom_interpreter = None
        self.custom_input_layer_index = 0
        self.custom_output_layer_index = 0

        # use the super class for handling the default models and load the custom ones in this one
        super().__init__(
            model_path=self.classifier_model_path,
            labels_path=self.classifier_labels_path,
            num_threads=num_threads,
        )

        self.load_model()
        self.load_labels()

    def load_model(self):
        """
        load_model _summary_
        """
        # load the default model

        self.interpreter = utils.load_model_from_file_tflite(
            self.model_path, num_threads=self.num_threads
        )

        # Get input and output tensors.
        input_details = self.interpreter.get_input_details()

        output_details = self.interpreter.get_output_details()

        # Get input tensor index
        self.input_layer_index = input_details[0]["index"]

        # Get classification output or feature embeddings as output, depending on presence fo custom classifier
        self.output_layer_index = output_details[0]["index"] - 1

        print("Default model loaded ")

        # now load the custom classifier
        self.custom_interpreter = utils.load_model_from_file_tflite(
            self.classifier_model_path, self.num_threads
        )

        input_details = self.custom_interpreter.get_input_details()

        output_details = self.custom_interpreter.get_output_details()

        self.custom_input_layer_index = input_details[0]["index"]

        self.custom_output_layer_index = output_details[0]["index"]
        print("Custom classifier loaded")

    def load_labels(self):
        """
        load_labels _summary_
        """

        labels = []
        with open(self.classifier_labels_path, "r") as lfile:
            for line in lfile.readlines():
                labels.append(line.replace("\n", ""))
        self.labels = labels
        print("Labels loaded.")

    def get_embeddings(self, data: np.array) -> np.array:
        """
        get_embeddings Extract feature embedding from audio file without immediatelly classifying the species.
                       These can in a second step be used with a custom classifier to find species not
                       included in the default training data.

        Args:
            data (np.array): Preprocessed audio snippet to extract features from

        Returns:
            np.array: Feature embedding produces by the default birdnet CNN.
        """
        self.interpreter.resize_tensor_input(
            self.input_layer_index, [len(data), *data[0].shape]
        )

        self.interpreter.allocate_tensors()

        # Extract feature embeddings
        self.interpreter.set_tensor(
            self.input_layer_index, np.array(data, dtype="float32")
        )

        self.interpreter.invoke()

        features = self.interpreter.get_tensor(self.output_layer_index)

        return features

    def predict(self, sample: np.array) -> np.array:
        """
        predict _summary_

        _extended_summary_

        Args:
            sample (np.array): _description_

        Returns:
            np.array: _description_
        """
        data = np.array(
            [
                sample,
            ],
            dtype="float32",
        )

        input_details = self.custom_interpreter.get_input_details()

        input_size = input_details[0]["shape"][-1]

        # get features from default model if the input size is compatible with the default model's feature vector output
        feature_vector = self.get_embeddings(data) if input_size != 144000 else data

        # use the feature vector as input of the self-trained classifier
        self.custom_interpreter.resize_tensor_input(
            self.custom_input_layer_index,
            [len(feature_vector), *feature_vector[0].shape],
        )

        self.custom_interpreter.allocate_tensors()

        # Make a prediction
        self.custom_interpreter.set_tensor(
            self.custom_input_layer_index, np.array(feature_vector, dtype="float32")
        )

        self.custom_interpreter.invoke()

        prediction = self.custom_interpreter.get_tensor(self.custom_output_layer_index)

        # map to probabilities
        probabilities = self._sigmoid(prediction, -self.sensitivity)

        return probabilities

    def _sigmoid(self, x, sensitivity=-1):
        """
        _sigmoid Apply a simple sigmoid to output logits to map to probabilities

        Args:
            logits (np.array): Raw output from a the inference function of the loaded model.
            sensitivity (float, optional): Sigmoid parameter. Defaults to -1.

        Returns:
            np.array: Model output mapped to [0,1] to get interpretable probability
        """
        return 1 / (1.0 + np.exp(sensitivity * np.clip(x, -15, 15)))

    @classmethod
    def from_cfg(cls, sparrow_dir: str, cfg: dict):
        """
        from_cfg _summary_

        _extended_summary_

        Args:
            cfg (dict): _description_

        Returns:
            _type_: _description_
        """

        # preprocess config because we need two models here
        cfg["default_model_path"] = str(Path(sparrow_dir) / Path("models") / Path("birdnet_default"))
        cfg["classifier_model_path"] = str(Path(sparrow_dir) / Path("models") / Path(cfg["model_path"]))

        del cfg["model_path"]
        return cls(**cfg)
