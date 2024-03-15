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
        apply_sigmoid: bool = True,
        sigmoid_sensitivity: float = 1.0,
        num_threads: int = 1,
        custom_species_list_path: str = None,
        custom_species_list: str = None,
        classifier_model_path: str = None,
        classifier_labels_path: str = None,
        default_model_path: str = None,
        default_labels_path: str = None,
    ):
        """
        __init__ Construct a new custom analyer from parameters or use defaults for those that are not provided.

        Args:
            apply_sigmoid (bool, optional): Whether to apply a sigmoid function to the final predictions. Defaults to True.
            sigmoid_sensitivity (float, optional): Sigmoid parameter. Defaults to 1.0.
            num_threads (int, optional): Number of threads to use for analysis. Defaults to 1.
            custom_species_list_path (str, optional): _description_. Defaults to None.
            custom_species_list (str, optional): _description_. Defaults to None.
            classifier_model_path (str, optional): _description_. Defaults to None.
            classifier_labels_path (str, optional): _description_. Defaults to None.
            default_model_path (str, optional): _description_. Defaults to None.
            default_labels_path (str, optional): _description_. Defaults to None.

        Raises:
            AnalyzerConfigurationError: If any one of the supplied paths is invalid.
        """
        # path checks
        if custom_species_list_path is not None:

            if Path(custom_species_list_path).exists() is False:
                raise AnalyzerConfigurationError(
                    "Custom species list path does not exist"
                )

        if custom_species_list is not None:

            if Path(custom_species_list).exists() is False:
                raise AnalyzerConfigurationError(
                    "Custom species list file does not exist"
                )

        if (
            classifier_model_path is not None
            and classifier_labels_path is None
            or classifier_model_path is None
            and classifier_labels_path is not None
        ):
            raise AnalyzerConfigurationError(
                "Model and label file paths must be specified to use a custom classifier"
            )

        if (
            classifier_model_path is not None
            and Path(classifier_model_path).exists() is False
        ):
            raise AnalyzerConfigurationError(
                "Custom classifier model could not be found at the provided path"
            )

        if (
            classifier_model_path is not None
            and Path(classifier_labels_path).exists() is False
        ):
            raise AnalyzerConfigurationError(
                "Custom classifier labels could not be found at the provided path"
            )

        if Path(default_model_path).exists() is False:
            raise AnalyzerConfigurationError(
                "Error, default model could not be found at provided path"
            )

        if Path(default_labels_path).exists() is False:
            raise AnalyzerConfigurationError(
                "Error, default label could not be found at provided path"
            )

        self.apply_sigmoid = apply_sigmoid
        self.sigmoid_sensitivity = sigmoid_sensitivity
        self.num_threads = num_threads
        self.custom_species_list_path = custom_species_list_path
        self.custom_species_list = custom_species_list
        self.classifier_model_path = classifier_model_path
        self.classifier_labels_path = classifier_labels_path
        self.default_model_path = default_model_path
        self.default_labels_path = default_labels_path

        super().__init__(
            custom_species_list_path=custom_species_list_path,
            custom_species_list=custom_species_list,
            classifier_model_path=self.classifier_model_path,
            classifier_labels_path=self.classifier_labels_path,
        )

    # README: these need to be overloaded because the base class uses hardcoded paths here. We don't.
    def load_model(self):
        """
        load_model Override of the base class load model to get the correct paths and make sure that we have multithreading
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
        # this is what the "embeddings" function in the normal BirdNET library does.
        # gets the feature embeddings from the
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

    def predict_with_custom_classifier(self, sample: np.array) -> list:
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

        data = np.array([sample], dtype="float32")

        input_details = self.custom_interpreter.get_input_details()

        input_size = input_details[0]["shape"][-1]

        feature_vector = self.get_embeddings(data) if input_size != 144000 else data

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

        # Logits or sigmoid activations?
        # self.apply_sigmoid = True # This is how it is done in birdnetlib-> ?
        if self.apply_sigmoid:
            # self.sigmoid_sensitivity = 1.0
            prediction = self.flat_sigmoid(
                np.array(prediction), sensitivity=-self.sigmoid_sensitivity
            )

        return prediction


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
