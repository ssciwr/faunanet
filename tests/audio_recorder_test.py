from iSparrow import audio_recording as ard
from pathlib import Path
import pyaudio
from datetime import datetime
import librosa


def test_audio_recorder_creation(folders, audio_recorder_fx):
    HOME, DATA, MODELS, OUTPUT, EXAMPLES = folders

    _, cfg = audio_recorder_fx

    recorder = ard.Recorder.from_cfg(cfg["Data"]["Recording"])

    assert recorder.output == DATA
    assert recorder.length_in_s == 5
    assert recorder.sample_rate == 48000
    assert recorder.file_type == "wav"
    assert recorder.channels == 1
    assert recorder.num_format == pyaudio.paInt16
    assert recorder.stream is None
    assert recorder.p is not None
    assert recorder.mode == "record"


def test_audio_recorder_recorder_functionality(folders, audio_recorder_fx):
    HOME, DATA, MODELS, OUTPUT, EXAMPLES = folders

    _, cfg = audio_recorder_fx

    recorder = ard.Recorder.from_cfg(cfg["Data"]["Recording"])

    # make sure the data folder is empty before doing anything
    for file in Path(recorder.output).iterdir():
        file.unlink()

    assert recorder.stream is None
    assert recorder.p is not None

    # support for stop condition is included in recorder
    class Condition:

        def __init__(self):
            self.x = 2

        def __call__(self, _):

            cond = self.x <= 0

            self.x -= 1

            return cond

    recorder.start(stop_condition=Condition())

    assert len(list(Path(recorder.output).iterdir())) == 2

    current = datetime.now().strftime("%y%m%d")

    files = list(Path(recorder.output).iterdir())

    for audiofile in files:
        yearmonthday = str(audiofile.name).split("_")[0]

        assert yearmonthday == current
        assert audiofile.suffix == ".wav"

        # read in file to test length, samplerate, num_samples

    with files[0] as audiofile:
        data, rate = librosa.load(
            Path(recorder.output) / audiofile, sr=48000, res_type="kaiser_fast"
        )

        duration = librosa.get_duration(y=data, sr=rate)

        assert rate == 48000

        # length must be sample rate (48000) times length in seconds (5)
        assert len(data) == 48000 * 5

        assert duration == 5
