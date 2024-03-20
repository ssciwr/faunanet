import tensorflow as tf
import tensorflow_hub as tfhub

try:
    import tflite_runtime as tflite
except Exception:
    from tensorflow import lite as tflite

from pathlib import Path
import validators as valid
import importlib


# custom exception to have some more control over what is raised
class TFModelException(Exception):
    pass


def is_url(potential_url: str) -> bool:
    """
    is_url Check whether the argument string represents a url


    Args:
        potential_url (str): String to check

    Returns:
        bool: Whether the argument represents a url (True) or not (False)
    """
    return True if valid.url(potential_url) else False


def load_model_from_file_tflite(path: str, num_threads: int = 1):
    """
    load_model_from_file_tflite Load model from a .tflite file.

    Args:
        path (str): Path to a .tflite model file to load
        num_threads (int, optional): Number of threads to use. Defaults to 1.

    Raises:
        FileNotFoundError: When the path given does not lead to an existing file
        TFModelException: When something goes wrong within tensorflow lite when loading the model or allocating tensors

    Returns:
        TensorflowLite interpreter: The loaded model
    """
    if Path(path).exists() is False:
        raise FileNotFoundError("The desired model file does not exist")

    try:
        interpreter = tflite.Interpreter(model_path=path, num_threads=num_threads)
        return interpreter
    except Exception as e:
        raise TFModelException(e)


def load_model_from_file_pb(path: str, _):
    """
    load_model_from_file_pb Load a tensorflow model saved as .pb in tensorflow's saved_model format from file. The file to be loaded must be named 'saved_model.pb'

    Args:
        path (str): Path to a floder containing 'saved_model.pb'

    Raises:
        FileNotFoundError: When the given path does not lead to a folder with a 'saved_model.pb' file in it.
        TFModelException: When something goes wrong inside tensorflow when loading the model.

    Returns:
        Tensorflow model: The loaded model
    """
    if "." in Path(path).name or ".pb" in Path(path).name:
        # tensorflow assumes a model file to be named "saved_model.pb" and the path given to be a directory
        path = Path(path).parent

    if Path(path).exists() is False:
        raise FileNotFoundError("The desired model file does not exist")

    try:
        model = tf.saved_model.load(path)
        return model
    except Exception as e:
        raise TFModelException(e)


def load_model_from_tensorflowhub(url: str, _):
    """
    load_model_from_hub Download a tensorflow model from tensorflow hub, ready to be used

    Args:
        url (str): URL leading to the model to be downloaded and used

    Raises:
        ValueError: When the argument is not a valid url
        TFModelException: When something goes wrong with the model loading inside the tensorflow_hub module

    Returns:
        Tensorflow model: The loaded model
    """
    if not is_url(url):
        raise ValueError(
            "The url given to load a model from tensorflow hub is not valid"
        )

    try:
        model = tfhub.load(url)
        return model
    except Exception as e:
        raise TFModelException(e)


def load_model_from_huggingfacehub(url: str, _):
    # TODO
    raise NotImplementedError("Huggingface hub is not yet supported")


def load_model_from_file_torch(path: str, _):
    """
    load_torch_model_from_file Load a torch model from file.

    Args:
        path (str): Path to a floder containing the model to be loaded.

    Raises:
        FileNotFoundError: When the given path does not lead to an existing file
        TFModelException: When something goes wrong inside torch when loading the model.

    Returns:
        torch model: The loaded model
    """
    raise NotImplementedError("torch models are not yet supported")


def load_module(alias: str, path: str):
    """
    load_module Load a python module from 'path' with alias 'alias'

    Args:
        path (str): Path to load the module from

    Returns:
        module: Python module that has been loaded
    """
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
