from iSparrow import utils
import pathlib
import yaml
import pandas as pd


class ModelFixture:

    def __init__(self, home, output, models):
        self.filepath = pathlib.Path(__file__).expanduser().resolve()
        self.testpath = self.filepath.parent.parent
        self.home = pathlib.Path(home).expanduser()
        self.output = pathlib.Path(output).expanduser()
        self.models_folder = pathlib.Path(models).expanduser()

        with open(self.testpath / pathlib.Path("test_configs") / "cfg_custom.yml", "r") as file:
            self.custom_cfg = yaml.safe_load(file)

        with open(
            self.testpath / pathlib.Path("test_configs") / "cfg_default.yml", "r"
        ) as file:
            self.default_cfg = yaml.safe_load(file)

        with open(
            self.testpath / pathlib.Path("test_configs") / "cfg_wrong_model.yml", "r"
        ) as file:
            self.cfg_wrong_model = yaml.safe_load(file)

        with open(self.testpath / pathlib.Path("test_configs") / "cfg_google.yml", "r") as file:
            self.google_cfg = yaml.safe_load(file)

        self.default_module = utils.load_module(
            "model_default",
            str(
                self.models_folder
                / pathlib.Path(self.default_cfg["Analysis"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.default_pp = utils.load_module(
            "pp_default",
            str(
                self.models_folder
                / pathlib.Path(self.default_cfg["Analysis"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        self.custom_module = utils.load_module(
            "model_custom",
            str(
                self.models_folder
                / pathlib.Path(self.custom_cfg["Analysis"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.google_module = utils.load_module(
            "model_google",
            str(
                self.models_folder
                / pathlib.Path(self.google_cfg["Analysis"]["Model"]["model_path"])
                / "model.py"
            ),
        )

        self.google_pp = utils.load_module(
            "pp_google",
            str(
                self.models_folder
                / pathlib.Path(self.google_cfg["Analysis"]["Model"]["model_path"])
                / "preprocessor.py"
            ),
        )

        ppd = self.default_pp.Preprocessor()

        data_default = ppd.read_audio_data(self.home / "example" / "soundscape.wav")

        self.data_default = ppd.process_audio_data(data_default)

        ppg = self.google_pp.Preprocessor()

        data_google = ppg.read_audio_data(self.home / "example" / "soundscape.wav")

        self.data_google = ppg.process_audio_data(data_google)

        # read data made with birdnet-Analysis for cross checking
        self.default_analysis_results = (
            pd.read_csv(
                self.testpath
                / pathlib.Path("stored_test_results")
                / pathlib.Path("default_results.csv")
            )
            .loc[:, ["scientific_name", "confidence"]]
            .sort_values(by="confidence", ascending=False)
        )

        self.custom_analysis_results = (
            pd.read_csv(
                self.testpath / pathlib.Path("stored_test_results") / pathlib.Path("custom_results.csv")
            )
            .loc[:, ["scientific_name", "confidence"]]
            .sort_values(by="confidence", ascending=False)
        )

        self.google_result = (
            (
                pd.read_csv(
                    self.testpath
                    / pathlib.Path("stored_test_results")
                    / pathlib.Path("google_results_minconf025.csv")
                ).sort_values(by="confidence", ascending=False)
            )
            .reset_index(drop=False)
            .rename(columns={"SCI_NAME": "scientific_name", "label": "labels"})
        )
