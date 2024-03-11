import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

try:
    import tflite_runtime.interpreter as tflite
except:
    from tensorflow import lite as tflite

from pathlib import Path

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
        self.input_details = None
        self.output_details = None
        self.input_layer_index = None
        self.output_layer_index = None
        self.labels = None
        self.n_threads = cfg["nthreads"]

        # load model

        self.interpreter = tflite.Interpreter(
            model_path=Path("iSparrow/models/birdnet_default/model.tflite"),
            n_threads=self.n_threads,
        )

        self.labels = self.load_labels("iSparrow/models/birdnet_default/labels.txt")

        self.interpreter.allocate_tensors()

        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Get input tensor index
        self.input_layer_index = self.input_details[0]["index"]

        # Get classification output or feature embeddings
        self.output_layer_index = self.output_details[0]["index"]

        print("Model loaded override")

    def load_labels(self, path: str) -> list:
        """
        load_labels _summary_

        _extended_summary_

        Args:
            path (str): _description_

        Returns:
            list: _description_
        """
        with open(path, "r") as lfile:
            for line in lfile.readlines():
                labels.append(line.replace("\n", ""))
        return labels

    def flat_sigmoid(self, x: np.array, sensitivity: float = -1) -> float:
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

    def apply_sigmoid(self, prediction: np.array) -> np.array:
        """
        apply_sigmoid _summary_

        _extended_summary_

        Args:
            prediction (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.flat_sigmoid(np.array(prediction), sensitivity=-SIGMOID_SENSITIVITY)

    def predict(self, sample: np.array) -> np.array:
        """
        predict _summary_

        _extended_summary_

        Args:
            sample (_type_): _description_
        """

        self.interpreter.resize_tensor_input(
            self.input_layer_index, [len(data), *data[0].shape]
        )
        self.interpreter.allocate_tensors()

        # Make a prediction (Audio only for now)
        self.interpreter.set_tensor(
            self.input_layer_index, np.array(data, dtype="float32")
        )
        self.interpreter.invoke()

        prediction = self.interpreter.get_tensor(self.output_layer_index)

        return prediction
