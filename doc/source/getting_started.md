# Getting started 
This page will provide you with a quick way to get a basic *Faunanet-lab* installation running. 
For further details, please refer to the linked pages for each section.  

## Installation
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
You have to fill in 'option' with either 'tensorflow' or 'tensorflow-lite'. The latter is only available on linux as a package. If you are using `zsh` as a shell (the default on macos), put quotes around the last part 
```zsh 
python3 -m pip install ".[option]"
```
then, you should be able to access the Faunanet-lab REPL by typing 'faunanet-lab' in your terminal: 
```bash 
faunanet-lab 
Welcome to Faunanet! Type help or ? to list commands 

(Faunanet) 
```
Then, you can enter commands to set up or start `Faunanet-lab` or interact with it.  

## Usage 

### As a standalone application 

### Directly from Python

### As a library in your own project 


