from birdnetlib.analyzer import Analyzer, AnalyzerConfigurationError
import numpy as np
from pathlib import Path


try:
    import tflite_runtime.interpreter as tflite
except Exception:
    from tensorflow import lite as tflite


class SparrowAnalyzer(Analyzer):
    """
    SparrowAnalyzer Specialization of birdnetlib.Analyzer to get the custom model to work

    """

    def __init__(
        self,
        model,
        apply_sigmoid: bool = True,
        sigmoid_sensitivity: float = 1.0,
    ):
        """
        __init__ Construct a new custom analyer from parameters or use defaults for those that are not provided.

        Args:
            model: Instance of a class derived from sparrow_models.ModelBase that represents a machine learning model for species identification
            apply_sigmoid (bool, optional): Whether to apply a sigmoid function to the final predictions. Defaults to True.
            sigmoid_sensitivity (float, optional): Sigmoid parameter. Defaults to 1.0.
        """

        self.apply_sigmoid = apply_sigmoid
        self.sigmoid_sensitivity = sigmoid_sensitivity
        self.model = model
        super().__init__(
            custom_species_list_path=self.model.custom_species_list_path,
            custom_species_list=self.model.custom_species_list,
            classifier_model_path=self.model.classifier_model_path,
            classifier_labels_path=self.model.classifier_labels_path,
        )

    # README: these are there to retain compatibility with birdnetlib
    @property
    def labels(self):
        return self.model.labels

    @property
    def default_model_path(self):
        return self.model.default_model_path

    @property
    def default_labels_path(self):
        return self.model.default_labels_path

    @property
    def num_threads(self):
        return self.model.num_threads

    @property
    def custom_species_list_path(self):
        return self.model.custom_species_list_path

    @property
    def custom_species_list(self):
        return self.model.custom_species_list

    @property
    def classifier_model_path(self):
        return self.model.classifier_model_path

    @property
    def classifier_labels_path(self):
        return self.model.classifier_labels_path

    # README: these need to be overloaded because the base class uses hardcoded paths here. We don't.
    def load_model(self):
        self.model.load_model()

    def load_labels(self):
        """
        load_labels Load labels for classes from file.

        """
        self.model.load_labels()

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
        return self.model.get_embeddings(data)

    def predict_with_custom_classifier(self, sample: np.array) -> list:
        # FIXME: this is probably not used anymore when we are done implementing stuff
        """
        predict_with_custom_classifier Extract features from supplied audio sample and classify them into bird species the classifier is trained upon.

        Args:
            sample (np.array): Preprocessed audio sample

        Returns:
            list: Probabilities with which the model thinks we have what species for each species known to it.
        """
        # overrides the predict_with_custom_classifier in the 'Analyzer' class
        # of birdnetlib with what the BirdNET-Analyzer system does.
        # README: will be replaced in a later PR with a more concise implementation

        predictions = self.model.predict(sample)

        if self.apply_sigmoid:
            predictions = self.flat_sigmoid(
                np.array(predictions), sensitivity=-self.sigmoid_sensitivity
            )

        return predictions

    def predict(self, sample: np.array) -> list:
        """
        predict TODO

        _extended_summary_

        Args:
            sample (np.array): _description_

        Returns:
            list: _description_
        """

        predictions = self.model.predict(sample)

        if self.apply_sigmoid:
            predictions = self.flat_sigmoid(
                np.array(predictions), sensitivity=-self.sigmoid_sensitivity
            )

        return predictions


def analyzer_from_config(sparrow_dir: str, cfg: dict) -> SparrowAnalyzer:
    """
    analyzer_from_config Create a new `SparrowAnalyzer` from a dict that contains parameters to be applied.
                         Dictionary typically results from reading in a YAML config file.
    Args:
        sparrow_dir (str): path to the top level directory where iSparrow stores its data
        cfg (dict): Dictionary containing the needed parameters

    Returns:
        SparrowAnalyzer: new `SparrowAnalyzer` instance.
    """
    apply_sigmoid = cfg["Model"]["apply_sigmoid"] if "" in cfg["Model"] else True

    sigmoid_sensitivity = (
        cfg["Model"]["sigmoid_sensitivity"] if "" in cfg["Model"] else 1.0
    )

    num_threads = cfg["Model"]["num_threads"] if "num_threads" in cfg["Model"] else 1

    # README:  the path treatment below is a temporary solution that will change again once the sparrow model itself is implemented.
    #          it will be generalized to arbitrary models and then be put there. This will also do away with the custom <-> default distinction
    custom_species_list_path = (
        str(Path(sparrow_dir) / Path(cfg["Model"]["custom_species_list_path"]))
        if "custom_species_list_path" in cfg["Model"]
        else None
    )

    custom_species_list = (
        cfg["Model"]["custom_species_list"]
        if "custom_species_list" in cfg["Model"]
        else None
    )

    # handle custom model paths and check they exist
    classifier_model_path = None

    classifier_labels_path = None

    # set them only when a model name is given explicitly and it's not default
    if "model_name" in cfg["Model"] and cfg["Model"]["model_name"] != "birdnet_default":

        classifier_model_path = (
            Path(sparrow_dir)
            / Path(cfg["Model"]["model_dir"])
            / Path(cfg["Model"]["model_name"])
            / Path("model.tflite")
        )

        classifier_labels_path = (
            Path(sparrow_dir)
            / Path(cfg["Model"]["model_dir"])
            / Path(cfg["Model"]["model_name"])
            / Path("labels.txt")
        )

        classifier_model_path = str(classifier_model_path)
        classifier_labels_path = str(classifier_labels_path)

    # the default path is only used in the derived class for now and must be checked
    # we always need those. Later: have a default config that's set up upon install and
    # that lives in .config on a unix system or similar
    default_model_path = (
        Path(sparrow_dir)
        / Path(cfg["Model"]["model_dir"])
        / "birdnet_default"
        / Path("model.tflite")
    )

    default_labels_path = (
        Path(sparrow_dir)
        / Path(cfg["Model"]["model_dir"])
        / "birdnet_default"
        / Path("labels.txt")
    )

    default_model_path = str(default_model_path)

    default_labels_path = str(default_labels_path)

    return SparrowAnalyzer(
        apply_sigmoid=apply_sigmoid,
        sigmoid_sensitivity=sigmoid_sensitivity,
        num_threads=num_threads,
        custom_species_list_path=custom_species_list_path,
        custom_species_list=custom_species_list,
        classifier_model_path=classifier_model_path,
        classifier_labels_path=classifier_labels_path,
        default_model_path=default_model_path,
        default_labels_path=default_labels_path,
    )
