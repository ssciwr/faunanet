import sys
from pathlib import Path
import numpy as np

from birdnetlib.analyzer import AnalyzerConfigurationError

sys.path.append("../../src/iSparrow")
from src.iSparrow.sparrow_model_base import ModelBase
import src.iSparrow.utils as utils


class GoogleModel(ModelBase):

    def __init__(self):
        pass

    def predict(self):
        pass

    def load_model(self):
        pass

    def load_labels(self):
        pass

    def postprocess_predictions(self):
        pass
