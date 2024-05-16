[![tests](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/ssciwr/iSparrow/graph/badge.svg?token=FwyE0PNiOk)](https://codecov.io/gh/ssciwr/iSparrow)

# iSparrow - Smart-IoT-based Passive bioAcoustic monitoRing of site-specific co-pResence of zOonotic Wildlife hosts and humans

iSparrow provides a flexible software for running bioacoustic classification machine learning systems on raspberry-Pi. By default, it uses the models provided by [Birdnet-Analyzer](https://github.com/kahst/BirdNET-Analyzer/tree/main), but can also use other models the user provides.

It achieves this by extending [birdnetlib](https://github.com/joeweiss/birdnetlib). 

## Features 
tbd 

## Usage
### Installation
Currently, iSparrow does not have a pypi package, so you need to install it from source. To do this, clone the repository, create a python virtual environment, and install iSparrow: 
```bash 
    cd path/to/dir/where/isparrow/should/live 

    git clone https://github.com/ssciwr/iSparrow.git

    python3 -m venv ./path/to/isparrow/venv

    source ./path/to/where/venv/bin/activate 

    cd ./iSparrow 

    python3 -m pip install .[tensorflow]  # or .[tensorflow-lite] for tflite models
``` 
On windows, the line ```source ./path/to/isparrow/venv/bin/activate``` must be replaced with 
```python3 ./path/to/isparrow/venv/scripts/activate```. You can also select which installation options you want in the last line, either ```tensorflow``` or ```tensorflow-lite```. Additionally, 
if you want to do further development, the installation must be modified by replacing the install command: 
```
    python3 -m pip install  -e .[tensorflow,tensorflow-lite]
    python3 -m pip install -r requirements-dev.txt
```

### Setup 
iSparrow needs three destinations on your filesystem in order to run: 
- a directory where the machine learning models for sound classification should be stored 
- a directory where incoming data files are stored. 
- a directory where the analysis results should be stored

iSparrow has a method `set_up` for this purpose, that is called with the path to a .yml configuration file. This file contains all the necessary information to set up a working iSparrow installation.
**This method must be called upon first usage in order to have a fully functioning iSparrow installation that documents its state correctly upon usage**. 
Below is an example of the structure iSparrow demands: 
```yaml 
Directories: 
  home: ~/iSparrow
  data: ~/iSparrow_data
  models: ~/iSparrow/models 
  output: ~/iSparrow_output
```
You can copy the above into a .yml file and customize the paths to whatever you want them to be. The `~` will be automatically expanded to the path to your home directory.
The method can be used as follows in python code

```python 
    from iSparrow import sparrow_setup as sps 
    filepath = Path("path", "to", "the", "install_config.yml")

    sps.set_up_sparrow(filepath)
```
It is important to have an outermost node called  `Directories`. Aside from creating the directories named in the installation config file, the installation method will download the default tensorflow models from [hugginface](https://huggingface.co/MaHaWo/iSparrow_test_models/tree/main) and will create `iSparrow` directories in you OS default config and cache folders. On Linux, these would be `~/.config` and `~/.cache`, respectively.

In the repl, this would work like this: 
```bash
   iSparrow # enter repl 

   set_up --cfg=./path/to/custom/install_config.yml 
``` 
This does the same as the call to ```sps.set_up_sparrow``` call above, so you can refer to the documentation of that function for further information, too. 

### Using iSparrow as a library 
iSparrow can be used as a library in your own application. Just add  
```python 
import iSparrow 
```
to have it available in your module, and make sure you use the correct virtual environment in which iSparrow is installed. Keep in mind that `iSparrow` in itself extends `birdnetlib`, so make sure to check the latter's documentation, too. 

### Running iSparrow 
iSparrow provides its own, small, REPL for interacting with a running instance. This can be used to start, stop, pause or continue it, to change classifier models or to query it's current state, input and output folders and so on. To get an overview over the available commands, you can just type  ```iSparrow``` in a terminal with the virtual environment being activated that iSparrow has been installed into. Alternatively, refer to the documentation.

