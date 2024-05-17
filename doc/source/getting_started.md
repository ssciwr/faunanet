# Getting Faunanet-lab up and running
This page will provide you with a quick way to get a basic *Faunanet-lab* installation running. 
For further details, please refer to the linked pages for each section.  

## Installation
### Installation for deployment
*Faunanet-lab* at the moment does not have a pypi release, hence it must be installed from source. To do so, open a terminal and follow the following steps. 
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

- navigate to the source base directory and install `Faunanet-lab`: 
```bash 
cd path/to/where/repo/should/go/Faunanet-lab
python3 -m pip install .[option]
```
You have to fill in 'option' with either 'tensorflow' or 'tensorflow-lite'. The latter is only available on linux as a package, and is especially relevant if you want to use `Faunanet-lab` on a small device like a RaspberryPi, because it is a lot more lightweight than tensorflow. If you are using `zsh` as a shell (the default on macos), put quotes around the last part: 
```zsh 
python3 -m pip install ".[option]"
```
After the installation has finishe, you should be able to access the Faunanet-lab REPL by typing 'faunanet-lab' in your terminal: 
```bash 
> faunanet-lab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) 
```
Then, you can enter commands to set up or start `Faunanet-lab` or interact with it.  

### Installation for development
Almost all steps stay the same, except it makes sense to install `Faunanet-lab` in editable and that you have to install the packages in the `requirements-dev.txt` file, too. 
```bash 
python3 -m pip install -e ".[option]"
python3 -m pip install -r requirements-dev.txt 
``` 

## Usage 

### As a standalone application
After installation, you can enter `Faunanet-lab` as described above. Before you can use it, it needs to be set up, which is done by the set-up command in the REPL: 

#### Creating a standard setup
```bash 
> faunanet-lab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) set-up 
```
This will create a default setup which creates folders `faunanet-lab`, `faunanet-lab/examples`, `faunanet-lab/models` and `faunanet-lab_output` in your home directory. 
Furthermore, there will be `standard_user_cache_directory/faunanet-lab` and `standard_user_config_directory/faunanet-lab`. `standard_user_c****_directory` is the operating-system dependent standard folder for configurations and cached files, e.g. `~/home/.cache` and `~/home/.config` on Linux. The setup configuration with all the folder paths will be copied to  `standard_user_config_directory/faunanet-lab/install.yml`. 
These folders serve the following purposes: 


| foldername|purpose|customizable|
| ----------|-------|------------|
| `faunanet-lab` | The home directory of `Faunanet-lab` where all the data needed to run it are stored.| Yes |
| `faunanet-lab`/`examples`| Example data needed for tests is stored here | No |
| `faunanet-lab/models` | Machine learning models along with the python code to use them with  `Faunanet-lab` are stored here | Yes |
| `user_cache_directory`/`faunanet-lab`  | The standard cache directory where `Faunanet-lab` puts files needing to be stored for further usage, e.g., computed species lists or the default machine learning models it downloads during setup. | No |
| `user_config_directory`/`faunanet-lab` | The standard config directory where `Faunanet-lab` stores its default configuration files.| No |

The presence of this file is used to determine if there is a `Faunanet-lab` folder already. Currently, `Faunanet-lab` does not have a dedicated `uninstall` method, so make sure to remove this file and all folders by hand if you want to get rid of an existing setup.


#### Customizing the setup 
The default `install.yml` file looks like this: 
```yaml 
Directories: 
  home: ~/faunanet-lab
  models: ~/faunanet-lab/models 
  output: ~/faunanet-lab_output
```
```{todo}
17/05/2024: Update this once the rest of the code is merged.
```
If you want to customize the locations of the folders that `Faunanet-lab` needs, you can provide your own `install.yml` file in which you customize these folders, e.g: 
```yaml 
Directories: 
  models: ~/faunanet_models 
  output: ~/faunanet_output
```
You only have to add the folders that you want to customize, `Faunanet-lab` will use the default values for everything else. The final installation config file `install.yml` that gets written by the `set-up` routine will then look like this: 
```yaml 
Directories: 
  home: ~/faunanet-lab
  models: ~/faunanet_models 
  output: ~/faunanet_output
```
In order to use you customized install file, run the setup metho from the REPL with the path to the config file as argument: 
```bash 
set-up --cfg=/path/to/custom/setupfile.yml 
``` 
See {doc}`basic_design` and {doc}`using_configuration_files` to learn more about how configuration files are used in `Faunanet-lab`. 

#### Starting a default `Faunanet-lab` instance 
The logic for starting a `Faunanet-lab` instance is the same as for the setup. There is a default set of parameters with which a `Faunanet-lab` instance can be started, and which can be customized 
via yaml files. To start a default instance, after you have completed the setup stage, run 
```bash 
(Faunanet) start 
``` 
The default configuration expects a folder `~/faunanet-lib_data` to exist in which audio files to be classified land. `Faunanet-lab` will then watch this folder indefinitely for incoming `.wav` files and analyze them. Results will be written to `~/faunanet-lib_output/ddmmyyyyy`, one csv-file at per incoming file. See {doc}`basic_design` to learn more about how `Faunanet-lab` handles results folders at startup. The `Faunanet-lab` watcher process will take note of any files landing subfolders of the data folder, too. 
By default, `Faunanet-lab` will use the birdnet-v.2.4 tflite model for classification. In order to see all parameters for this model as well as the other default models that `Faunanet-lab` provides, see {doc}`using_configuration_files`. To see what else you can do with the REPL, see {doc}`repl_usage`. 

The easiest way to provide your own model to use with `Faunanet-lab` is to retrain the `Birdnet-Analyzer` model as described [here](https://github.com/kahst/BirdNET-Analyzer?tab=readme-ov-file#training). Models obtained in this way will use the same set of configuration parameters as the default model, so customization is achiedved most easily. For more details about how to use your own model, see {doc}`using_custom_models`. 


### As a library in your own project
Once `Faunanet-lab` is installed, you can use 
```python 
import Faunanet-lab
``` 
to get access to the basic functionality. 
Please refer to {doc}`iSparrow_api_doc` for the code documentation.


