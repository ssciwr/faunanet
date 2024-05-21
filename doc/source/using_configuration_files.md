# Using configuration files
Configuration files in `faunanet-lab` are used to centralize where and how parameters are passed 
to the system. They are stored in yaml files which allows for ease of use and extendibility.
Configuration files are always in the `yaml` format. `faunanet-lab` uses configuration files for its setup and for the usage of machine learning models for audio classification. 

## Default configuration structure for instantiating `faunanet-lab` with a given model
### Basic concepts
The configuration file with which to start a `faunanet-lab` instance is called `run_config` here.
Using a machine learning model with `faunanet-lab` for analyzing audio data proceeds always in two steps, data preprocessing and the application of the model to the preprocessed data. These steps need to be parameterized by the config files. Additionally, 
we can have parameters that tell us about geographic location or time, confidence thresholds for the classification results and many more.
```{important}
As  a general rule, the nodes for Recording, Model, SpeciesPresence and Preprocessor contain default arguments for the parameters of the `FauanentRecording, ModelBase, SpeciesPredictorBase and PreprocessorBase` classes respectively. See their documentation for what these are. 
The Analysis-node as a whole provides the defaults for the FaunanetWatcher class.
```
### Description of the default configuration to be supplied with models
Therefore, `faunanet-lab` expects a `run_config` to have two top-level nodes: `Analysis` and `Data`. The former parameterized the model application, the latter the data preprocessing. 

The `Data` node needs a subnode `Preprocessor` which gives values for the instantiation of the used preprocessor. Secondly, it must have `input` and `output` nodes for `faunanet-lab` to know where it should look for data and where is should put the results. In total the structure of the `Data` node must be as follows: 

```yaml
Data: 
    input: path_to_where_to_look_for_data
    output: path_to_where_to_create_batch_folders
    Preprocessor: 
        param1: value1 
        param2: value2
        ....
``` 

The `Analysis` node is more complex because it encompasses more steps. It expects two subnodes: 
- `Recording` The parameterization of the `FaunanetRecording` class. 
- `Model` The parameterization of the classifier to be used, which internally is an implementation of the `ModelBase` class. 
The following additional nodes must be provided: 
- **modelname**: Name of the folder a model is stored in the `faunanet-lab`'s model folder. See {doc}`using_custom_models` for details. 
- **pattern**: The file extension pattern of the incoming data files, e.g., `.wav`.
- **check_time**: How often `faunanet-lab` should poll the input folder for new data.
- **delete_recordings**: When to delete the raw data files in the input directory. Can be 'always' (delete immediatelly) or 'never' (keep them around forever).

If the `SpeciesPredictor` system shall be used, we need an additional Node `SpeciesPresence` that contains: 
- **threshold**: Above this output value, a species is considered to be possibly present at the locale at the given time. Below, it is not.
- **num_thread**: Number of threads to use for prediction.
- **use_cache**: Boolean flag that tells whether the predicted species precense should be cached or not.
The minimum structure of a **any** default config file supplied with a model therefore **must** be: 
```yaml
Analysis:
  # For managing the loading and processing audio files 
  Recording:
    # threshold above which a species is interpreted as being possibly present or not.
    species_presence_threshold: float in [0, 1]
    # threshold above which a detection is considered valid.
    min_conf: float in [0, 1]
    # Time interval for the system to check if a file to be analyzed is still being written to
    file_check_poll_interval: integer > 0
    # latitude of audio file recording: Set to null if species should not be filtered or if the model doesn't support it.
    lat: float in [-90, 90]
    # longitude of audio file recording: Set to null if species should not be filtered or if the model doesn't support it
    lon: float in [-180, 180)
    # date of audio file recording. Set to null if species should not be filtered or if the model doesn't support it
    date: either 'today' or string in dd/MM/yy format. 
  # For the actual model inference
  Model:
    # number of threads used to run the model for inference. Only relevant for tflite models. 
    num_threads: integer > 0
  # For the species presence predictor if used. Otherwise ignored. If set to null, (lat, lon, date) must all be null, too.
  SpeciesPresence:
    # number of threads used to run the model for inference.
    num_threads: integer > 0
    # whether to cache the results of the species prediction for each (lat, lon, date) combination
    use_cache: bool in [true, false]

  # name of the model to be used. must correspond to a folder in Faunanetlab_home/models. By default, this is ~/Faunanetlab/models.
  modelname: model name. possible by default are 'birdnet_default', 'birdnet_custom', 'google_perch'
  # file extension of the audio files to look for
  pattern: string, e.g., '.wav' or '.mp3'
  # how often to check for new files. Must be integer > 0
  check_time: n > 0
  # whether to delete audio files after analysis or not.
  delete_recordings: 'always' or 'never'

Data: 
  # input directory where the audio files to analyze land. They can be in any subdirectory of this, too.
  input: ~/faunanet-lab_data
  # directory where the analysis results should be written to
  output: ~/faunanet-lab_output
  # Node that parameterizes the preprocessor instance
  Preprocessor: 
    # sample rate the audio files should be resampled to
    sample_rate: integer > 0. typically 48000 or 32000
    # overlab between samples.
    overlap: float > 0
    # length of each analyzed sample
    sample_secs: float > 0
    # possible resample method. If librosa is used, check its supported resample types, or the resample methods of whatever library your preprocessor implementation uses.
    resample_type: string, e.g., kaiser_fast
```
Additional parameters for the `Preprocessor` and `Model` nodes must be provided if the `Model` or `Preprocessor` implementations of the used classifier require them.

```{important}
Models obtained through the birdnet-Analyzer retraining feature customize the list of species. Hence, the custom model provided with `Faunanetlab` does not support the `SpeciesPredictor`. 
```

For example, the default configuration file for the default birdnetV2.4 model looks like this: 
```yaml 
Analysis: 
  Recording:
    species_presence_threshold: 0.03
    min_conf: 0.25
    file_check_poll_interval: 1
    lat: 42.5
    lon: -76.45
    date: today
  Model:
    sigmoid_sensitivity: 1.0
    num_threads: 2
    species_list_file: null

  SpeciesPresence: 
    threshold: 0.03
    num_threads: 1
    use_cache: true

  modelname: birdnet_default
  pattern: ".wav"
  check_time: 1
  delete_recordings: "never"

Data: 
  input: ~/faunanet-lab_data
  output: ~/faunanet-lab_output
  Preprocessor:
    sample_rate: 48000
    overlap: 0.0
    sample_secs: 3.0
    resample_type: kaiser_fast
```
When you run `faunanet-lab` without any arguments from the repl, it runs with this set of parameters.

## Setup configuration 
Like the actual usage, the setup of `faunanet-lab` is also controlled via a yaml configuration file. 
This file has a simple structure and consists currently only of a list of directories that should 
be created. 
```yaml 
Directories: 
  home: ~/faunanet-lab 
  models: ~/faunanet-lab/models
  output: ~/faunanet-lab_output
```
The same customization logic as for the run configurations described above applies here, too. See {doc}`Installation <getting_started>` for how to customize a Fauanetlab installation.
This file will be written to to the default config path of your system into a folder called `faunanet-lab`. On Linux, this would be `~/.config/faunanet-lab/install.yml`. 


## Running `faunanet-lab` with custom parameters 
For each task (setup, run), a default configuration is (or must be by the model supplier) provided. Individual elements of this can then be overridden by user supplied config files. `faunanet-lab` always uses the default config of the model as the basis. If provided, it then loads the supplied user config and replaces all the entries in the default config with the respective entries in the user config.

Consequently, only entries that are present in the default config can be overridden: A default config **must always be complete**, i.e., it must fully define the respective element it shall parameterize, e.g., model or preprocessor. To give an example: 

The default config could be: 
```yaml
Node: 
    A: 
        a: 1
        c: 2 
    B: 
        x: 4
Node: 
    X: 
        v: 3
``` 
which then can be updated by the following user config: 
```yaml
Node: 

    B: 
        x: -2
Node: 
    X: 
        v: 88
```
into
```yaml
Node: 
    A: 
        a: 1
        c: 2 
    B: 
        x: -2
Node: 
    X: 
        v: 88
``` 
Additional parameters in the user config not present in the default config will silently be ignored. All shipped models have their own default config, and all custom models must come with a `default.yml` file.

For example, a customization of the default configuration for the default model to make it run with a different location and date can look like this: 
```yaml 
Analysis: 
  Recording:
    lat: 52.52
    lon: 13.40
    date: 12/01/23
  modelname: birdnet_default
``` 
Or, to use the google-perch model, you could provide the following user config: 
```yaml 
Analysis: 
    model_name: google_perch
  Recording:
    # species presence predictor not supported by perch
    lat: null
    lon: null
    date: null
Data:
  # adjust preprocessor data to what google-perch expects
  Preprocessor:
    sample_rate: 32000
    sample_secs: 5.0
```