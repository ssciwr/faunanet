from pathlib import Path
import importlib.util
import os
import time
import yaml
import inspect


# custom exception to have some more control over what is raised
class TFModelException(Exception):
    pass


def get_method_docstring(cls, method_name: str) -> str:
    """
    get_method_docstring Retrieve the docstring of a class method.

    Args:
        method_name (_type_): Name of the method to retrieve the docstring from

    Returns:
        str: Method docstring
    """
    # Get the method object from the class
    method = getattr(cls, method_name, None)
    if method is None:
        return None

    # Get the docstring of the method
    docstring = inspect.getdoc(method)
    return docstring


def update_dict_leafs_recursive(base, update):
    """
    update_dict_leafs_recursive Merge recursively two arbitrarily nested dictionaries such that only those leaves of 'base' are upated with the content of 'update' for which the given path in 'update' fully exists in 'base'.

    This function assumes that nodes in 'base' are only replaced, and 'update' does not add new nodes.

    Args:
        base (dict): Base dictionary to update.
        update (dict): dictionary to update 'base' with.
    """
    # basic assumption: update is a sub-tree of base with unknown entry point.
    if isinstance(base, dict) and isinstance(update, dict):

        for kb, vb in base.items():
            if kb in update:
                # overlapping element branch found
                if isinstance(vb, dict) and isinstance(update[kb], dict):
                    # follow branch if possible
                    update_dict_leafs_recursive(vb, update[kb])
                else:
                    # assign if not
                    base[kb] = update[kb]
            else:
                update_dict_leafs_recursive(vb, update)  # find entrypoint
    else:
        pass  # not found and no dictionaries - pass


def read_yaml(path: str):
    print(f"...reading config from {path}")
    """
        read_yaml Read the yaml basic config file for faunanet from path.
                It contains the install directory, data directory and other things used
                by faunanet internally.

        Args:
            path (str): Path to the yaml base config.

        Returns:
            dict: read base config file.
        """

    if Path(path).exists() is False:
        raise FileNotFoundError(f"The folder {path} does not exist")

    with open(Path(path)) as file:
        base_cfg = yaml.safe_load(file)

    return base_cfg


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
    try:
        import tflite_runtime.interpreter as tflite
    except Exception:
        from tensorflow import lite as tflite

    if Path(path).exists() is False:
        raise FileNotFoundError(f"The desired model file does not exist: {path}")

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
    import tensorflow as tf

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


def load_module(module_name: str, file_path: str):
    """
    load_module Load a python module from 'path' with alias 'alias'

    Args:
        module_name (str): module alias.
        file_path (str): Path to load the module from

    Returns:
        module: Python module that has been loaded
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        raise RuntimeError(f"Error in loading module {file_path}") from e
    return module


def load_name_from_module(module_name: str, file_path: str, name: str):
    """
    load_name_from_module Load a python module from 'path' with alias 'alias'

    Args:
        module_name (str): module alias.
        file_path (str): Path to load the module from
        name (str): name to import
    Returns:
        module: Python module that has been loaded
    """
    module = load_module(module_name, file_path)
    return getattr(module, name)


def wait_for_file_completion(file_path: str, polling_interval=1) -> bool:
    """
    wait_for_file_completion Wait for a file to be fully written by checking when its size does no longer change.

    Args:
        file_path (str): filepath to check
        polling_interval (int, optional): how often file size should be checked. Defaults to 1.

    Returns:
        bool: True when the file size does not change any longer. False otherwise
    """
    initial_size = os.path.getsize(file_path)
    is_complete = False
    while True:

        time.sleep(polling_interval)

        current_size = os.path.getsize(file_path)

        if current_size == initial_size:
            is_complete = True
            break
        else:
            initial_size = current_size
    return is_complete
