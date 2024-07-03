[![tests](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/ssciwr/iSparrow/graph/badge.svg?token=FwyE0PNiOk)](https://codecov.io/gh/ssciwr/iSparrow)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ssciwr_iSparrow&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=ssciwr_iSparrow)
[![Supported OS: Linux | macOS | Windows](https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20Windows-green.svg)](https://www.linux.org/)
[![Documentation](https://readthedocs.org/projects/isparrow/badge/?version=latest)](https://isparrow.readthedocs.io/en/latest/?badge=latest)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# faunanet - A bioacoustics platform based on birdnetlib using neural networks 
## What is faunanet? 
`faunanet` is an extension of [*Birdnet-Analyzer*](https://github.com/kahst/BirdNET-Analyzer), and uses [*birdnetlib*](https://github.com/joeweiss/birdnetlib) as its basis. 
`faunanet` was developed with the goal to provide a platform for bioacoustics research projects, started at the Interdisciplinary center for scientific computing at the University of Heidelberg. 

## Features
Using the birdnetv2.4 model by default, `faunanet` provides three core features: 

- Easily and arbitrarily exchange the underlying maching learning model for bioacoustics.
- Easy configuration using YAML files which are stored alongside the analysis results. 
- Integrated, extendible REPL with which to interact with which to interact with a running instance.

The main element of `faunanet` is a 'watcher' class that continuously monitors a folder for incoming data files and allows for on-the-fly model- or parameter-change via the REPL. It can also be used as a library in your python project.
By extending elements of bridnetlib rather, `faunanet` conserves the latter's capabilities while still adding its own functionality on top of it. 

## Getting started 
Please refer to the 'Getting faunanet up and running' section in the documentation for an introduction. 

## Bugs, issues and feature requests
Please use the [issue tab of the github page](https://github.com/ssciwr/iSparrow/issues) to report any bugs or feature requests. 

## Contributions 
Feel free to contribute to this project by opening a pull request [here](https://github.com/ssciwr/iSparrow/pulls). 

## Usage
### Installation
Make sure that ffmpeg is installed on your system: 
```bash
# for debian based linux
sudo apt install ffmpeg
```
or for macOS using homebrew:
```bash 
brew install ffmpeg
```
On windows, you can use chocolatey or other package managers to the same effect: 
```bash
choco install ffmpeg
```
ffmpeg is needed for the audio preprocessing that is done by faunanet when analyzing your data.

You can install `faunanet` from pip with 
```bash 
pip install faunanet[option]
```
with option being "tensorflow" for the full tensorflow suite, or "tensorflow-lite" to install only the `tflite_runtime` package which only provides restricted support for model operations, while full tensorflow supports all models built with it. Installing it from pip will install the newest release version of `faunanet`. **One of the two is needed to run `faunanet`, with `tensorflow` being the appropriate one for most usecases.** 

You can also install it from source to get the latest development chagnes. To do this, clone the repository, create a [python virtual environment](https://docs.python.org/3/library/venv.html), and install `faunanet`into it: 
```bash 
    cd path/to/dir/where/faunanet/should/live 

    git clone https://github.com/ssciwr/iSparrow.git

    python3 -m venv ./path/to/faunanet/venv

    source ./path/to/where/venv/bin/activate 

    cd ./faunanet 

    python3 -m pip install .[tensorflow]  # or .[tensorflow-lite] for tflite models
``` 
On windows, the line ```source ./path/to/faunanet/venv/bin/activate``` must be replaced with 
```python3 ./path/to/faunanet/venv/scripts/activate```. You can also select which installation options you want in the last line, either ```tensorflow``` or ```tensorflow-lite```. Additionally, 
if you want to do further development, the installation must be modified by replacing the install command, adding 'editable' mode and development dependencies.
```
    python3 -m pip install  -e .[tensorflow, dev]
```

For building the documentation locally, you have to install with yet another set of dependencies: 

### Setup 
faunanet needs three destinations on your filesystem in order to run: 
- a directory where the machine learning models for sound classification should be stored 
- a directory where incoming data files are stored. 
- a directory where the analysis results should be stored

faunanet has a method `set_up` for this purpose, that is called with the path to a .yml configuration file. This file contains all the necessary information to set up a working faunanet installation.
**This method must be called upon first usage in order to have a fully functioning faunanet installation that documents its state correctly upon usage**. 
Below is an example of the structure faunanet demands: 
```yaml 
Directories: 
  home: ~/faunanet
  data: ~/faunanet_data
  models: ~/faunanet/models 
  output: ~/faunanet_output
```
You can copy the above into a .yml file and customize the paths to whatever you want them to be. The `~` will be automatically expanded to the path to your home directory.
The method can be used as follows in python code

```python 
    from faunanet import faunanet_setup as sps 
    filepath = Path("path", "to", "the", "install_config.yml")

    sps.set_up(filepath)
```
It is important to have an outermost node called  `Directories`. Aside from creating the directories named in the installation config file, the installation method will download the default tensorflow models from [hugginface](https://huggingface.co/MaHaWo/faunanet_test_models/tree/main) and will create `faunanet` directories in you OS default config and cache folders. On Linux, these would be `~/.config` and `~/.cache`, respectively.

In the repl, this would work like this: 
```bash
   faunanet # enter repl 

   set_up --cfg=./path/to/custom/install_config.yml 
``` 
This does the same as the call to ```sps.set_up``` call above, so you can refer to the documentation of that function for further information, too. 

### Using faunanet as a library 
faunanet can be used as a library in your own application. Just add  
```python 
import faunanet 
```
to have it available in your module, and make sure you use the correct virtual environment in which faunanet is installed. Keep in mind that `faunanet` in itself extends `birdnetlib`, so make sure to check the latter's documentation, too. 

### Running faunanet 
faunanet provides its own, small, REPL for interacting with a running instance. This can be used to start, stop, pause or continue it, to change classifier models or to query it's current state, input and output folders and so on. To get an overview over the available commands, you can just type  ```faunanet``` in a terminal with the virtual environment being activated that faunanet has been installed into. Alternatively, refer to the documentation.


### Using the docker image

#### Run the docker-hub image
You can also run `faunanet` in docker by pulling the latest `faunanet` image from docker-hub and 
running it via terminal command: 
```bash
docker run -ti --rm \ 
     -v /path/on/host/for/faunanet/configs:/root/faunanet_config \
     -v /path/on/host/for/faunanet/output:/root/faunanet_output \ 
     -v /path/on/host/for/faunanet/models:/root/faunanet/models \ 
     -v /path/on/host/for/faunanet/data:/root/faunanet_data \ 
     mahawo/faunanet_{OPTION}:latest
```
Of special interest are the mounted volumes, i.e., the paths behind the `-v` arguments: 
- first: for config files 
- second: for analysis output 
- third: for models 
- forth: for incoming data. If you run the system via docker compose (see below) in conjunction with faunanet-record you do not need this, because `faunanet-record` will take care of this folder. 

`{OPTION}` corresponds to `tf` for tensorflow or `tflite` for tensorflow-lite.

#### Built the image yourself
To built the dockerfile that comes with the package yourself you can use the following docker command: 
```bash
docker build --build-arg INSTALL_OPTION=TENSORFLOW_OPTION \
    -t your-dockerhub-username/your-image-name:tag \
    -f path/to/Dockerfile .
```
Where the `TENSORFLOW_OPTION` has to be replaced with either `tensorflow` or `tensorflow-lite`. The dockerfile itself is very simple and can be modified to your liking.
```dockerfile
FROM python:3.11-slim

WORKDIR /root

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg -y --no-install-recommends && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION

# install with the necessary option
RUN pip install faunanet[${INSTALL_OPTION}]
WORKDIR /root

RUN mkdir /root/faunanet_config 

# add entrypoint
CMD ["faunanet"]
```

In order to build an image for the ARM64 architecture often used by raspberry PI or other edge devices, you can use `docker buildx` in conjunction with `qemu` (tested on linux machine):

```bash
 docker buildx build --platform=linux/arm64 -t containername:tag -f ~/path/to/docker/file/dockerfile.dockerfile . --push
```
Have a look [here](https://www.docker.com/blog/multi-arch-images/) for more info.

#### Using `faunanet` with other services via docker compose
`faunanet` can be run together with `faunanet-record` using [docker compose](https://docs.docker.com/compose/) or together with other containers of your choice. You can use the following docker-compose file as a starting point, which also comes with the installation: 
```yaml 
services:
  faunanet:
    image: mahawo/faunanet:latest
    tty: true 
    stdin_open: true
    volumes:
      - ~/faunanet/config:/root/faunanet_config
      - ~/faunanet/output:/root/faunanet_output
      - ~/faunanet/models:/root/faunanet/models
      - ~/faunanet/data:/root/faunanet_data
    environment:
      - RUN_CONFIG=analysis_config.yml
  faunanet_record:
    image: mahawo/faunanet_record:latest
    tty: true 
    stdin_open: true
    volumes:
      - ~/faunanet/config:/root/faunanet_config
      - ~/faunanet/data:/root/faunanet_data
    devices:
      - /dev/snd:/dev/snd # this needs to be the microphone device
    environment:
      - RUN_CONFIG=record_config.yml
```
To locate the files from an existing pip installation, use the following python script, or pull them from the `docker` directory in `faunanet` home directory after it has been set up (see [Setup](#Setup)). The environment variables `RUN_CONFIG` for each service here can hold the name of config files that are stored in the directory mounted into `/root/faunanet_config`.

When working with config files for the docker version, make sure to refer to the folders within the docker container and not the local ones. Otherwise, the system will fail with a 