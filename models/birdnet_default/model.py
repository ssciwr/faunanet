from pathlib import Path
import numpy as np

from iSparrow.sparrow_model_base import ModelBase

# from iSparrow import utils


class Model(ModelBase):
    """
    Model Model class representing the the default birdnet model. Does currently not support custom species list or species prediction based on coordinates.

    """

    def __init__(
        self,
        model_path: str,
        num_threads: int = 1,
        sigmoid_sensitivity: float = 1.0,
        species_list_file: str = None,
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

        labels_path = str(Path(model_path) / "labels.txt")

        model_path = str(Path(model_path) / "model.tflite")

        # base class loads the model and labels
        super().__init__(
            "birdnet_default_model",
            model_path,
            labels_path,
            num_threads=num_threads,
            sensitivity=sigmoid_sensitivity,
        )

        # store input and output index to not have to retrieve them each time an inference is made
        input_details = self.model.get_input_details()

        output_details = self.model.get_output_details()

        # Get input tensor index
        self.input_layer_index = input_details[0]["index"]

        # Get classification output or feature embeddings as output, depending on presence fo custom classifier
        self.output_layer_index = output_details[0]["index"]

    def load_species_list(self):
        # TODO
        pass

    def predict(self, sample: np.array) -> np.array:
        """
        predict Make inference about the bird species for the preprocessed data passed to this function as arguments.

        Args:
            data (np.array): list of preprocessed data chunks
        Returns:
            list: List of (label, inferred_probability)
        """
        data = np.array([sample], dtype="float32")

        self.model.resize_tensor_input(
            self.input_layer_index, [len(data), *data[0].shape]
        )
        self.model.allocate_tensors()

        # Make a prediction (Audio only for now)
        self.model.set_tensor(self.input_layer_index, np.array(data, dtype="float32"))
        self.model.invoke()

        prediction = self.model.get_tensor(self.output_layer_index)

        confidence = self._sigmoid(np.array(prediction), sensitivity=-self.sensitivity)

        return confidence

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
            Path(sparrow_folder) / Path("models") / cfg["model_path"]
        )

        return cls(**cfg)
