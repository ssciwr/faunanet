from birdnetlib.analyzer import Analyzer
import numpy as np 


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
        self.apply_sigmoid = cfg['Model']['apply_sigmoid']
        self.sigmoid_sensitivity = cfg['Model']['sigmoid_sensitivity']
        super().__init__()

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
        # I'm not quite sure why this is important and what happens?
        # get embeddings data --> why does this work? what does it do? 
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
        # why does this work? no idea... 
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
