import tensorflow_hub as hub
import tensorflow as tf
import numpy as np

model_path = "https://kaggle.com/models/google/bird-vocalization-classifier/frameworks/TensorFlow2/variations/bird-vocalization-classifier/versions/2"

model = hub.load(model_path)

waveform = np.zeros(5 * 32000, dtype=np.float32)

logits, embeddings = model.infer_tf(waveform[np.newaxis, :])

print(type(model))

model_path = "/home/hmack/iSparrow/models/google_perch"

model = tf.saved_model.load(model_path)

waveform = np.zeros(5 * 32000, dtype=np.float32)

pb_logits, pb_embeddings = model.infer_tf(waveform[np.newaxis, :])

print(type(model))
