import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = ""


try:
    import tflite_runtime.interpreter as tflite
except:
    from tensorflow import lite as tflite

from pathlib import Path
import numpy as np

from iSparrow import sparrow_model_abstract as sma


class Model(sma.AbstractModel):
    """
    Model _summary_

    _extended_summary_

    Args:
        ABC (_type_): _description_
    """

    def __init__(self, cfg: dict):
        """
        __init__ _summary_

        _extended_summary_

        Args:
            cfg (dict): _description_
        """

        self.apply_sigmoid = cfg["apply_sigmoid"]
        self.sigmoid_sensitivity = cfg["sensitivity"]
        self.interpreter = None
        self.input_layer_index = None
        self.output_layer_index = None
        self.labels = None
        self.n_threads = cfg["num_threads"]
        self.custom_input_layer_index = None
        self.custom_output_layer_index = None
        self.custom_interpreter = None

        # load model
        self.interpreter = tflite.Interpreter(
            model_path=os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "birdnet_defaults",
                "model.tflite",
            ),
            num_threads=self.n_threads,
        )

        self.interpreter.allocate_tensors()

        # Get input tensor index
        self.input_layer_index = self.interpreter.get_input_details()[0]["index"]

        # Get classification output for feature embeddings
        self.output_layer_index = self.interpreter.get_output_details()[0]["index"] - 1

        # set up custom classifier
        self.custom_interpreter = tflite.Interpreter(
            model_path=os.path.join(os.path.dirname(__file__), "model.tflite"),
            num_threads=self.n_threads,
        )

        self.custom_interpreter.allocate_tensors()

        self.custom_input_layer_index = self.custom_interpreter.get_input_details()[0][
            "index"
        ]

        self.custom_output_layer_index = self.custom_interpreter.get_output_details()[
            0
        ]["index"]

        self.labels = self.load_labels(
            os.path.join(os.path.dirname(__file__), "labels.txt")
        )

        print("custom classifier model loaded override")

    def flat_sigmoid(self, x, sensitivity=-1):
        """
        flat_sigmoid _summary_

        _extended_summary_

        Args:
            x (_type_): _description_
            sensitivity (int, optional): _description_. Defaults to -1.

        Returns:
            _type_: _description_
        """
        return 1 / (1.0 + np.exp(sensitivity * np.clip(x, -15, 15)))

    def apply_sigmoid(self, prediction):
        """
        apply_sigmoid _summary_

        _extended_summary_

        Args:
            prediction (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.flat_sigmoid(np.array(prediction), sensitivity=-SIGMOID_SENSITIVITY)

    def get_embeddings(self, sample):
        """_summary_

        Args:
            sample (_type_): _description_

        Returns:
            _type_: _description_
        """
        data = np.array([sample], dtype="float32")

        # this is what the "embeddings" function in the normal BirdNET library does.
        # I'm not quite sure why this is important and what happens?
        # get embeddings data --> why does this work? what does it do?
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

    def predict(self, sample):
        """
        predict _summary_

        _extended_summary_

        Args:
            sample (_type_): _description_
        """

        # when using a custom classifier, we use the default CNN to get
        # feature embeddings, then use the custom classifier and apply it to
        # the features to get the classification

        embeddings = self.get_embeddings(sample)

        data = np.array([sample], dtype="float32")

        input_details = self.custom_interpreter.get_input_details()

        output_details = self.custom_interpreter.get_output_details()

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
        if self.apply_sigmoid:
            prediction = self.flat_sigmoid(
                np.array(prediction), sensitivity=-self.sigmoid_sensitivity
            )

        return prediction
