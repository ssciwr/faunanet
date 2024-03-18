import pytest

from birdnetlib.analyzer import AnalyzerConfigurationError
from pathlib import Path


def default_model_construction(model_fx):
    mfx = model_fx()

    model = mfx.module.Model.from_cfg(mfx.cfg_default["Analyzer"]["Model"])

    assert 3 == 4
