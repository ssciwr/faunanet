from abc import ABC, abstractmethod
import numpy as np


class PreprocessorBase(ABC):
    """
    PreprocessorBase A common interface for all custom preprocessor classes

    """
    @abstractmethod
    def read_audio_data(self, path: str) -> np.array:
        """
        read_audio_data Read in audio data from a path and return it in a form that can be used by a 'process_audio_data' implementation.


        Args:
            path (str): Path to the audio file to read
        """

        pass

    @abstractmethod
    def process_audio_data(self, rawdata: np.ndarray) -> list:
        """
        process_audio_data Receives raw read data and processes it into something that can be used by the analyzer model.


        Args:
            rawdata (np.ndarray): Raw audiodata received from the read_audio_data function.

        Returns:
            list: final preprocessed audiodata ready to be passed to the analyzer
        """
        
        pass
