[![tests](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/ssciwr/iSparrow/graph/badge.svg?token=FwyE0PNiOk)](https://codecov.io/gh/ssciwr/iSparrow)

# iSparrow - Smart-IoT-based Passive bioAcoustic monitoRing of site-specific co-pResence of zOonotic Wildlife hosts and humans

iSparrow provides a flexible software for running bioacoustic classification machine learning systems on raspberry-Pi. By default, it uses the models provided by [Birdnet-Analyzer](https://github.com/kahst/BirdNET-Analyzer/tree/main), but can also use other models the user provides.

It achieves this by extending [birdnetlib](https://github.com/joeweiss/birdnetlib). 

## Features 
tbd 

## Installation 
tbd 


## Usage
When you first start using iSparrow, you need to set up a folder structure where models will be stored, analysis results will be written to and so on. iSparrow has a method `set_up` for this purpose, that is called with the path to a .yml configuration file. 
**This method must be called upon first usage in order to have a fully functioning iSparrow installation that documents its state correctly upon usage**. 
The installation config file must contain all these necessary paths. Below is an example of the structure iSparrow demands: 

```yaml 
Directories: 
  home: ~/iSparrow
  data: ~/iSparrow_data
  models: ~/iSparrow/models 
  output: ~/iSparrow_output
```

You can copy the above into a .yml file and customize the paths to whatever you want them to be. The `~` will be automatically expanded to the path to your home directory.
The method can be used as follows: 

```python 
    filepath = Path("path", "to", "the", "install_config.yml")

    sps.set_up_sparrow(filepath)
```

It is important to have an outermost node called  `Directories`. Aside from creating the directories named in the installation config file, the installation method will download the default tensorflow models from [hugginface](https://huggingface.co/MaHaWo/iSparrow_test_models/tree/main) and will create `iSparrow` directories in you OS default config and cache folders. On Linux, these would be `~/.config` and `~/.cache`, respectively.

