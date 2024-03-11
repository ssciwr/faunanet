import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import importlib

import birdnetlib as bnl

from src.iSparrow import analyzer as ana
from src.iSparrow import recording as rec
from src.iSparrow import preprocessor as pre

# home = Path.home()/ Path('Development/iSparrow')
home = Path.home() / Path(
    "Library/CloudStorage/SeaDrive-HaraldMack(heibox.uni-heidelberg.de)/Meine Bibliotheken/iSparrow"
)
with open(home / "tests/test.yml", "r") as file:
    cfg = yaml.safe_load(file)

pp = importlib.import_module(
    "models." + cfg["Analyzer"]["Model"]["path"] + ".preprocessor"
)

preprocessor = pp.Preprocessor()

classifier = ana.SparrowAnalyzer(
    classifier_model_path=str(
        home / Path("models") / Path(cfg["Analyzer"]["Model"]["path"]) / "model.tflite"
    ),
    classifier_labels_path=str(
        home / Path("models") / Path(cfg["Analyzer"]["Model"]["path"]) / "labels.txt"
    ),
)

recording = rec.SparrowRecording(
    classifier,
    preprocessor,
    cfg["Data"]["input"] + "/soundscape.wav",
    min_conf=0.25,
)

recording.analyze()

df = pd.DataFrame(recording.detections).sort_values(by="confidence")
df.to_csv(home / Path("tests") / "custom_results.csv")

print(df)

recording = rec.SparrowRecording(
    ana.SparrowAnalyzer(),
    preprocessor,
    cfg["Data"]["input"] + "/soundscape.wav",
    min_conf=0.25,
)

recording.analyze()

df = pd.DataFrame(recording.detections).sort_values(by="confidence")
df.to_csv(home / Path("tests") / "default_results.csv")

print(df)
