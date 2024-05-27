# Getting faunanet-lab up and running
This page will provide you with a quick way to get a basic `faunanet-lab` installation running. 
For further details, please refer to the respective topic pages.  

## Installation
### Installation for production
`faunanet-lab` at the moment does not have a pypi release, hence it must be installed from source. To do so, open a terminal and follow the below steps. 
You need a python3.9 or higher installation that is accessible from your standard path. A way to create virtual environments is also strongly recommended, typically this would be `conda` or `python-venv`. We will use `venv` here. We furthermore assume a unix shell here, though the steps on windows are equivalent.

- navigate to where you want the repository to go: 
```bash
cd path/to/where/repo/should/go
```
- clone the repository: 
```bash 
git clone git@github.com:ssciwr/iSparrow.git # for using https: https://github.com/ssciwr/iSparrow.git
``` 
- make a new python virtual environment and activate it 
```bash
python -m venv path/to/venv/venvname # creation of venv
source path/to/venv/venvname/bin/activate # activation
```

on Windows, the venv has to be activated by: 
```bash
python3 path/to/venv/scripts/activate 
```

- navigate to the source base directory and install `faunanet-lab`: 
```bash 
cd path/to/where/repo/should/go/faunanet-lab
python3 -m pip install .[option]
```
You have to fill in 'option' with either 'tensorflow' or 'tensorflow-lite'. The latter is only available on Linux as a package, and is especially relevant if you want to use `faunanet-lab` on a small device like a RaspberryPi, because it is a lot more lightweight than tensorflow. If you are using `zsh` as a shell (the default on macos), put quotes around the last part: 
```zsh 
python3 -m pip install ".[option]"
```
After the installation has finished, you should be able to access the faunanet-lab REPL by typing 'faunanet-lab' in your terminal: 
```bash 
> faunanet-lab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) 
```
Then, you can enter commands to set up or start `faunanet-lab` or interact with it.  

### Installation for development
Almost all steps stay the same, except it makes sense to install `faunanet-lab` in editable and that you have to install the packages in the `requirements-dev.txt` file, too. 
```bash 
python3 -m pip install -e ".[option]"
python3 -m pip install -r requirements-dev.txt 
``` 

## Setup and usage 

### Usage as library in your own project
Once `faunanet-lab` is installed, you can use 
```python 
import faunanet-lab
``` 
to get access to the basic functionality. 
Please refer to {doc}`iSparrow_api_doc` for the code documentation.


### As a standalone application
After installation, you can enter `faunanet-lab` as described above. Before you can use it, it needs to be set up, which is done by the set-up command in the REPL: 

#### Creating a standard setup
```bash 
> faunanet-lab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) set-up 
```
This will create a default setup which creates folders `faunanet-lab`, `faunanet-lab/examples`, `faunanet-lab/models` and `faunanet-lab_output` in your home directory. 
Furthermore, there will be `user_cache_directory/faunanet-lab` and `user_config_directory/faunanet-lab`. `user_c****_directory` is the operating-system dependent standard folder for configurations and cached files, e.g. `~/home/.cache` and `~/home/.config` on Linux. The setup configuration with all the folder paths will be copied to  `user_config_directory/faunanet-lab/install.yml`. 

#### Customizing the setup 
The `faunanet-lab` setup can be customized by providing a custom installation configuration file `install.yml`.
The default `install.yml` file looks like this: 
```yaml 
Directories: 
  home: ~/faunanet-lab
  models: ~/faunanet-lab/models 
  output: ~/faunanet-lab_output
```

The specified folders serve the following purposes: 

| foldername                             | purpose                                                                                                                                                                                             | customizable |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `faunanet-lab`                         | The home directory of `faunanet-lab` where all the data needed to run the package is stored                                                                                                                 | Yes          |
| `faunanet-lab`/`examples`              | Example data needed for tests is stored here                                                                                                                                                        | No           |
| `faunanet-lab/models`                  | Machine learning models along with the Python wrappers for  `faunanet-lab` are stored here                                                                                                 | Yes          |
| `user_cache_directory`/`faunanet-lab`  | The standard cache directory where `faunanet-lab` puts files needing to be stored for further usage, e.g., computed species lists or the default machine learning models it downloads during setup. | No           |
| `user_config_directory`/`faunanet-lab` | The standard config directory where `faunanet-lab` stores its default configuration files.                                                                                                          | No           |

The presence of this file is used to determine if there is a `faunanet-lab` folder already. Currently, `faunanet-lab` does not have a dedicated `uninstall` method, so make sure to remove this file and the folder containing it by hand if you want to get rid of an existing setup.

If you want to customize the locations of the folders that `faunanet-lab` needs, you can provide your own `install.yml` file in which you customize these folders, e.g: 
```yaml 
Directories: 
  models: ~/faunanet_models 
  output: ~/faunanet_output
```
You only have to add the folders that you want to customize, `faunanet-lab` will use the default values for everything else. The final installation config file `install.yml` that gets written by the `set-up` routine will then look like this: 
```yaml 
Directories: 
  home: ~/faunanet-lab
  models: ~/faunanet_models 
  output: ~/faunanet_output
```
In order to use you customized install file, run the setup method from the REPL with the path to the config file as argument: 
```bash 
set-up --cfg=/path/to/custom/setupfile.yml 
``` 
See {doc}`basic_design` and {doc}`using_configuration_files` to learn more about how configuration files are used in `faunanet-lab`. 

### Removing a `faunanet-lab` setup 
There can only be one `faunanet-lab` setup on any machine at any given time. There is currently no dedicated `uninstall` method, so you have to remove a setup by hand if you want a new one. 
In `faunanet-lab`'s shell, you can use the `get_setup_info` command to get the locations of all the folders used by `faunanet-lab`. All the folders listed there need to be removed in order to remove an existing setup. The following walks you throught the process of removing an existing setup by hand. 
- Enter the `faunanet-lab` shell and enter `get_setup_info` to get all the folders to delete.
- Delete all folders listed in it under `Directories` in the output: Per default, the file looks like shown before and the relevant folders are the ones shown in the table above.
- Delete all folders listed under `cache directories` to remove downloaded files.
- Delete all folders listed under `config directories` to remove existing config files.
After this procedure, you should be able to setup faunanet lab anew as described before. 
If you want to delete `faunanet-lab` itself, use pip from the virtual environment you installed it in: 
```bash
python3 -m pip uninstall faunanet-lab 
```

### Starting a default `faunanet-lab` instance 
After a setup has been created, `faunanet-lab` can be started. 
The logic for starting a `faunanet-lab` instance is the same as for the setup. There is a default set of parameters with which a `faunanet-lab` instance can be started, and which can be customized 
via yaml files. To start a default instance, after you have completed the setup stage, run 
```bash 
(Faunanet) start 
``` 
The default configuration expects a folder `~/faunanet-lab_data` to exist where audio files should be placed for subsequent classification. `faunanet-lab` will then watch this folder indefinitely for incoming `.wav` files and analyze them. Results will be written to `~/faunanet-lib_output/ddmmyyyyy`, one csv-file at per incoming file. See {doc}`basic_design` to learn more about how `faunanet-lab` handles results folders at startup. The `faunanet-lab` watcher process will take note of any files landing in subfolders of the data folder, too. 
By default, `faunanet-lab` will use the birdnet-v.2.4 tflite model for classification. In order to see all parameters for this model as well as the other default models that `faunanet-lab` provides, see {doc}`using_configuration_files`. To see what else you can do with the REPL, see {doc}`repl_usage`. 

### Use custom parameters for a `faunanet-lab` instance
If you want to customize the parameters this instance is run with, you once more have to provide a custom configuration file: 
```bash
(Faunanet) start --cfg=/path/to/custom/run.yml 
```
The general structure of such a file is described in {doc}`using_configuration_files`. A model to be used with `faunanet-lab` must provide its own complete set of default parameters. The default model and example models ship these upon setup. 
The easiest way to provide your own model to use with `faunanet-lab` is to retrain the `Birdnet-Analyzer` model as described [here](https://github.com/kahst/BirdNET-Analyzer?tab=readme-ov-file#training). Models obtained in this way will use the same set of parameters as the default model, so customization is easy. For more details about how to use your own model, see {doc}`using_custom_models`. 
You can also change the model on the fly via the `change_analyzer` command. This command works almost identically to the `start` command. See the documentation of the REPL {doc}`repl_usage` for more.

## Contribution 
Issue- or bug reports and feature requests as well as code contributions are welcome here: https://github.com/ssciwr/iSparrow