from abc import ABC, abstractmethod
import numpy as np
from pathlib import Path
import operator
from . import utils


class ModelBase(ABC):
    """
    ModelBase Base model class for iSparrow. Every model that iSparrow can use must derive from this class.

    Attributes:
        model_path (str): path to the model file used, or the url used to load it
        labels_path (str): path to the labels file read for having labels
        species_list_path (str|None): Path to a restricted list of species labels if used, else None
        sensitivity (float, defaults to 1.0): Parameter of the sigmoid activation function used to produce classification probabilities.
    """

    def __init__(
        self,
        name: str,
        model_path: str,
        labels_path: str,
        num_threads: int = 1,
        sensitivity: float = 1.0,
    ):
        self.num_threads = num_threads

        if Path(model_path).exists() is False:
            raise FileNotFoundError(f"No model file at {model_path}")

        if Path(labels_path).exists() is False:
            raise FileNotFoundError(f"No labels file at {labels_path}")

        self.name = name

        self.model_path = model_path

        self.labels_path = labels_path

        self.sensitivity = sensitivity

        self.results = None

        self.load_model()

        self.load_labels()

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
        }

        # get the model file
        model_filename = str(Path(self.model_path).name)

        # load model locally

        if model_filename not in model_loaders:
            raise ValueError(f"Model filename unknown: {model_filename}")

        self.model = model_loaders[model_filename](self.model_path, self.num_threads)

    @abstractmethod
    def predict(self, data: np.array) -> list:
        pass

    def analyze_recording(self, recording):
        """
        analyze_recording _summary_

        Args:
            recording (_type_): _description_
        """
        print("name of model: ", self.name)
        start = 0
        end = recording.processor.sample_secs
        results = {}
        for c in recording.processor.chunks:

            # make predictions and put together with labels
            predictions = self.predict(c)[0]

            labeled_predictions = list(zip(self.labels, predictions))

            # Sort by score and filter
            sorted_predictions = sorted(
                labeled_predictions, key=operator.itemgetter(1), reverse=True
            )

            # Filter by recording.minimum_confidence so not to needlessly store full array for each chunk.
            labeled_predictions_filtered = [
                i for i in sorted_predictions if i[1] >= recording.minimum_confidence
            ]

            # Store results
            results[(start, end)] = labeled_predictions_filtered

            # Increment start and end
            start += recording.processor.sample_secs - recording.processor.overlap
            end = start + recording.processor.sample_secs

            self.results = results
