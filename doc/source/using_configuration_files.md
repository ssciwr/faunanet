# Using configuration files
Configuration files in `Faunanetlab` are used to centralize where and how parameters are passed 
to the system. They are stored in yaml files which allows for ease of use and extendibility.
Configuration files are always in the `yaml` format. `Faunanetlab` uses configuration files for its setup and for the usage of machine learning models for audio classification. 

## Default and user configurations
For each task (setup, run), a default configuration is (or must be by the model supplier) provided. Individual elements of this can then be overridden by user supplied config files. `Faunanetlab` always uses the default config as the basis. If provided, it then loads the supplied user config and replaces all the entries in the default config with the respective entries in the user config.

Consequently, only entries that are present in the default config can be overridden, a default config **must always be complete**, i.e., it must fully define the respective element it shall parameterize, e.g., model or preprocessor. To give an example: 

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

### Providing default configuration files for your own model
The configuration file with which to start a `Faunanetlab` instance is called `run_config` here.
Using a machine learning model with `Faunanet-lib` for analyzing audio data proceeds always in two steps, data preprocessing and the application of the model to the preprocessed data. Additionally, 
we can have parameters that tell us about geographic location or time, confidence thresholds for the classification results and many more. These can parameterize additional steps, e.g., prediction of the species present based on time and coordinates. 
Therefore, `Faunanetlab` expects a `run_config` to have two top-level nodes: `Analysis` and `Data`. The former parameterized the model application, the latter the data preprocessing. 

The `Data` node needs a subnode `Preprocessor` which gives values for the instantiation of the preprocessor that's used. Secondly, it must have `input` and `output` nodes for `Faunanetlab` to know where it should look for data and where is should put the results. In total the structure of the `Data` node must be as follows: 

```yaml 
input: path_to_where_to_look_for_data
output: path_to_where_to_create_batch_folders
Preprocessor: 
    param1: value1 
    param2: value2
    ....
``` 

The `Analysis` node is more complex because it encompasses more steps It expects two subnodes: 
- `Recording` The parameterization of the `SparrowRecorder` class. 
- `Model` The parameterization of the classifier to be used. 
The following additional nodes must be provided: 
- **modelname**: Name of the folder a model is stored in in `Faunanetlab`'s model folder. See {doc}`using_custom_models` for details. 
- **pattern**: The file extension pattern of the incoming data files, e.g., `.wav`.
- **check_time**: How often `Fauanet-lab` should poll the input folder for new data.
- **delete_recordings**: When to delete the raw data files in the input directory. Can be 'always' (delete immediatelly) or 'never' (keep them around forever).

If the `SpeciesPredictor` system shall be used, we need an additional Node `SpeciesPresence` that contains: 
- **threshold**: Above this output value, a species is considered to be possibly present at the locale at the given time. Below, it is not.
- **num_thread**: Number of threads to use for prediction. 
- **use_cache**: Boolean flag that tells whether the predicted species precense should be cached or not.
  
```{todo}
Make this into a highlight box 
```
**Important** The birdnet-Analyzer retraining feature customizes the list of species. Hence, it does not support the `SpeciesPredictor`. 

```{todo}
17/05/2024: Check again if the num_threads thing does anything
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
  input: ~/Faunanetlab_data
  output: ~/Faunanetlab_output
  Preprocessor:
    sample_rate: 48000
    overlap: 0.0
    sample_secs: 3.0
    resample_type: kaiser_fast
```

## Setup configuration 
Like the actual usage, the setup of Faunanetlab is also controlled via a yaml configuration file. 
This file has a simple structure and consists currently only of a list of directories that should 
be created. 
```yaml 
Directories: 
  home: ~/Faunanetlab 
  models: ~/Faunanetlab/models
  output: ~/Faunanetlab_output
```
  
```{todo}
add missing stuff once rest of code is merged
```
The same customization logic as for the run configurations described above applies here, too. See {doc}`Installation <getting_started>` for how to customize a Fauanetlab installation.
This file will be written to to the default config path of your system into a folder called `Faunanetlab`. On Linux, this would be `~/.config/Faunanetlab/install.yml`. 

