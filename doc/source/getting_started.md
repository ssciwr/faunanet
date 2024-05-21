# Getting Faunanetlab up and running
This page will provide you with a quick way to get a basic `Faunanetlab` installation running. 
For further details, please refer to the respective topic pages.  

## Installation
### Installation for production
`Faunanetlab` at the moment does not have a pypi release, hence it must be installed from source. To do so, open a terminal and follow the following steps. 
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

- navigate to the source base directory and install `Faunanetlab`: 
```bash 
cd path/to/where/repo/should/go/Faunanetlab
python3 -m pip install .[option]
```
You have to fill in 'option' with either 'tensorflow' or 'tensorflow-lite'. The latter is only available on Linux as a package, and is especially relevant if you want to use `Faunanetlab` on a small device like a RaspberryPi, because it is a lot more lightweight than tensorflow. If you are using `zsh` as a shell (the default on macos), put quotes around the last part: 
```zsh 
python3 -m pip install ".[option]"
```
After the installation has finishe, you should be able to access the Faunanetlab REPL by typing 'faunanetlab' in your terminal: 
```bash 
> faunanetlab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) 
```
Then, you can enter commands to set up or start `Faunanetlab` or interact with it.  

### Installation for development
Almost all steps stay the same, except it makes sense to install `Faunanetlab` in editable and that you have to install the packages in the `requirements-dev.txt` file, too. 
```bash 
python3 -m pip install -e ".[option]"
python3 -m pip install -r requirements-dev.txt 
``` 

## Usage 

### As a standalone application
After installation, you can enter `Faunanetlab` as described above. Before you can use it, it needs to be set up, which is done by the set-up command in the REPL: 

#### Creating a standard setup
```bash 
> faunanetlab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) set-up 
```
This will create a default setup which creates folders `faunanetlab`, `faunanetlab/examples`, `faunanetlab/models` and `faunanetlab_output` in your home directory. 
Furthermore, there will be `user_cache_directory/faunanetlab` and `user_config_directory/faunanetlab`. `user_c****_directory` is the operating-system dependent standard folder for configurations and cached files, e.g. `~/home/.cache` and `~/home/.config` on Linux. The setup configuration with all the folder paths will be copied to  `user_config_directory/faunanetlab/install.yml`. 

#### Customizing the setup 
The `Faunanetlab` setup can be customized by providing a custom installation configuration file
The default `install.yml` file looks like this: 
```yaml 
Directories: 
  home: ~/faunanetlab
  models: ~/faunanetlab/models 
  output: ~/faunanetlab_output
```
```{todo}
17/05/2024: Update this once the rest of the code is merged.
```
The specified folders serve the following purposes: 

| foldername                            | purpose                                                                                                                                                                                            | customizable |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| `faunanetlab`                         | The home directory of `Faunanetlab` where all the data needed to run it are stored.                                                                                                                | Yes          |
| `faunanetlab`/`examples`              | Example data needed for tests is stored here                                                                                                                                                       | No           |
| `faunanetlab/models`                  | Machine learning models along with the python code to use them with  `Faunanetlab` are stored here                                                                                                 | Yes          |
| `user_cache_directory`/`faunanetlab`  | The standard cache directory where `Faunanetlab` puts files needing to be stored for further usage, e.g., computed species lists or the default machine learning models it downloads during setup. | No           |
| `user_config_directory`/`faunanetlab` | The standard config directory where `Faunanetlab` stores its default configuration files.                                                                                                          | No           |

The presence of this file is used to determine if there is a `Faunanetlab` folder already. Currently, `Faunanetlab` does not have a dedicated `uninstall` method, so make sure to remove this file and all folders by hand if you want to get rid of an existing setup.

If you want to customize the locations of the folders that `Faunanetlab` needs, you can provide your own `install.yml` file in which you customize these folders, e.g: 
```yaml 
Directories: 
  models: ~/faunanet_models 
  output: ~/faunanet_output
```
You only have to add the folders that you want to customize, `Faunanetlab` will use the default values for everything else. The final installation config file `install.yml` that gets written by the `set-up` routine will then look like this: 
```yaml 
Directories: 
  home: ~/faunanetlab
  models: ~/faunanet_models 
  output: ~/faunanet_output
```
In order to use you customized install file, run the setup metho from the REPL with the path to the config file as argument: 
```bash 
set-up --cfg=/path/to/custom/setupfile.yml 
``` 
See {doc}`basic_design` and {doc}`using_configuration_files` to learn more about how configuration files are used in `Faunanetlab`. 

#### Removing a `Faunanetlab` setup 
There can only be one `Faunanetlab` setup on any machine at any given time. There is currently no dedicated `uninstall` method, so you have to remove a setup by hand if you want a new one. In order to remove an existing setup: 
- Check the standard user config directory of your system for a folder `faunanetlab`. Therein, open the `install.yml` file.
You can have a look [here](https://pypi.org/project/platformdirs/) to see the standard user config paths for your platform, or use 
```python 
from platformdirs import user_config_dir, user_cache_dir 

user_config_dir() 

user_cache_dir() 
``` 
to get the user config and user cache directories directly. 
- Delete all folders listed in it under `Directories`. Per default, the file looks like shown above and the relevant folders are the one shown in the above table. 
  Delete the `faunanetlab` folder in the user config directory.
- Go to the standard user cache directory and delete all folders containing `faunanetlab` in their name. This will remove all downloaded model files and cached species lists. 

in a python shell started from the `faunanetlab` virtual environment to get their location directly.
After this procedure, you should be able to setup faunanet lab anew as described before. 

#### Starting a default `Faunanetlab` instance 
The logic for starting a `Faunanetlab` instance is the same as for the setup. There is a default set of parameters with which a `Faunanetlab` instance can be started, and which can be customized 
via yaml files. To start a default instance, after you have completed the setup stage, run 
```bash 
(Faunanet) start 
``` 
The default configuration expects a folder `~/faunanetlab_data` to exist in which audio files to be classified land. `Faunanetlab` will then watch this folder indefinitely for incoming `.wav` files and analyze them. Results will be written to `~/faunanet-lib_output/ddmmyyyyy`, one csv-file at per incoming file. See {doc}`basic_design` to learn more about how `Faunanetlab` handles results folders at startup. The `Faunanetlab` watcher process will take note of any files landing subfolders of the data folder, too. 
By default, `Faunanetlab` will use the birdnet-v.2.4 tflite model for classification. In order to see all parameters for this model as well as the other default models that `Faunanetlab` provides, see {doc}`using_configuration_files`. To see what else you can do with the REPL, see {doc}`repl_usage`. 

#### Use custom parameters for a `Faunanetlab` instance
If you want to customize the parameters this instance is run with, you once more have to provide a custom configuration file: 
```bash
(Faunanet) start --cfg=/path/to/custom/run.yml 
```
The general structure of such a file is described in {doc}`using_configuration_files`. A model to be used with `Faunanetlab` must provide its own complete set of default parameters. The default model and example models ship these upon setup. 
The easiest way to provide your own model to use with `Faunanetlab` is to retrain the `Birdnet-Analyzer` model as described [here](https://github.com/kahst/BirdNET-Analyzer?tab=readme-ov-file#training). Models obtained in this way will use the same set of parameters as the default model, so customization is easy. For more details about how to use your own model, see {doc}`using_custom_models`. 

### As a library in your own project
Once `Faunanetlab` is installed, you can use 
```python 
import Faunanetlab
``` 
to get access to the basic functionality. 
Please refer to {doc}`iSparrow_api_doc` for the code documentation.


