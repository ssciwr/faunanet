from birdnetlib.analyzer import Analyzer, AnalyzerConfigurationError
import numpy as np
from pathlib import Path


try:
    import tflite_runtime.interpreter as tflite
except:
    from tensorflow import lite as tflite


class SparrowAnalyzer(Analyzer):
    """
    SparrowAnalyzer Specialization of birdnetlib.Analyzer to get the custom model to work

    Args:
        Analyzer (_type_): _description_
    """

    def __init__(self, cfg: dict):
        """
        __init__ _summary_

        _extended_summary_
        """
        self.apply_sigmoid = cfg["Model"]["apply_sigmoid"] if "" in cfg["Model"] else True

        self.sigmoid_sensitivity = cfg["Model"]["sigmoid_sensitivity"] if "" in cfg["Model"] else 1.0

        self.num_threads = cfg["Model"]["num_threads"] if "num_threads" in cfg["Model"] else 1

        # README:  the path treatment below is a temporary solution that will change again once the sparrow model itself is implemented.
        #          it will be generalized to arbitrary models and then be put there. This will also do away with the custom <-> default distinction
        custom_species_list_path = cfg["Model"]["custom_species_list_path"] if "custom_species_list_path" in cfg["Model"] else None

        custom_species_list = cfg["Model"]["custom_species_list"] if "custom_species_list" in cfg["Model"] else None

        if Path(custom_species_list_path).exists() is False:
            raise AnalyzerConfigurationError("custom species list path does not exist")

        if Path(custom_species_list).exists() is False:
            raise AnalyzerConfigurationError("custom species list file does not exist")

        if "path" not in cfg["Model"] or cfg["Model"]["path"] != "birdnet_default":
            if (Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("model.tflite")).exists() is False:
                raise AnalyzerConfigurationError("model file does not exist")

            if (Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("labels.txt")).exists() is False:
                raise AnalyzerConfigurationError("labels file does not exist")

            classifier_model_path = str(Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("model.tflite"))

            classifier_labels_path = str(Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("labels.txt"))

        else:
            if (Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("model.tflite")).exists() is False:
                raise AnalyzerConfigurationError("default model file does not exist")

            if (Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("labels.txt")).exists() is False:
                raise AnalyzerConfigurationError("default labels file does not exist")

            self.default_model_path = Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("model.tflite")

            self.default_labels_path = Path(cfg["Model"]["model_dir"]) / Path(cfg["Model"]["model_name"]) / Path("labels.txt")

        super().__init__(custom_species_list_path=custom_species_list_path,
                         custom_species_list=custom_species_list,
                         classifier_model_path=classifier_model_path,
                         classifier_labels_path=classifier_labels_path)

    def load_model(self):
        """
        load_model Override of the base class load model to get the correct paths and make sure that we have multithreading
        """
        self.interpreter = tflite.Interpreter(model_path=str(self.default_model_path), num_threads=self.num_threads)
        self.interpreter.allocate_tensors()

        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Get classification output or feature embeddings
        if self.use_custom_classifier:
            self.output_layer_index = self.output_details[0]["index"] - 1
        else:
            self.output_layer_index = self.output_details[0]["index"]

        print("Model loaded.")

    def get_embeddings(self, data):
        """
        get_embeddings _summary_

        _extended_summary_

        Args:
            data (_type_): _description_

        Returns:
            _type_: _description_
        """
        # this is what the "embeddings" function in the normal BirdNET library does.
        # gets the feature embeddings from the
        self.interpreter.resize_tensor_input(self.input_layer_index, [len(data), *data[0].shape])
        self.interpreter.allocate_tensors()

        # Extract feature embeddings
        self.interpreter.set_tensor(self.input_layer_index, np.array(data, dtype="float32"))
        self.interpreter.invoke()
        features = self.interpreter.get_tensor(self.output_layer_index)

        return features

    def predict_with_custom_classifier(self, sample):
        """
        predict_with_custom_classifier _summary_

        _extended_summary_

        Args:
            sample (_type_): _description_

        Returns:
            _type_: _description_
        """
        # overrides the predict_with_custom_classifier in the 'Analyzer' class
        # of birdnetlib with what the BirdNET-Analyzer system does.
        # FIXME: will be replaced in a later PR with a more concise implementation

        data = np.array([sample], dtype="float32")

        input_details = self.custom_interpreter.get_input_details()

        input_size = input_details[0]["shape"][-1]

        feature_vector = self.get_embeddings(data) if input_size != 144000 else data

        self.custom_interpreter.resize_tensor_input(
            self.custom_input_layer_index, [len(feature_vector), *feature_vector[0].shape]
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
