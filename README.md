[![tests](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/ssciwr/iSparrow/graph/badge.svg?token=FwyE0PNiOk)](https://codecov.io/gh/ssciwr/iSparrow)

# Faunanetlab
`Faunanetlab` is an extension of [*Birdnet-Analyzer*](https://github.com/kahst/BirdNET-Analyzer), and uses [*birdnetlib*](https://github.com/joeweiss/birdnetlib) as its basis. 
`Faunanetlab` was developed with the goal to provide a platform for bioacoustics research projects, started at the Interdisciplinary center for scientific computing at the University of Heidelberg. 

## Features
Using the basic birdnet-model by default, `Faunanetlab` provides three core features: 

- The possibilty to easily and arbitrarily exchange the underlying maching learning model
- Easy configuration using YAML files which are stored alongside the analysis results 
- An integrated, extendible REPL with which to interact with which to interact with a running instance.

The main element of `Faunanetlab` is a 'watcher' system that continuously monitors a folder for incoming data files and allows for on-the-fly model- or parameter-change via the REPL. It can also be used as a library in your python project.   

## Getting started 
Please refer to the 'Getting started' section in the documentation for an introduction. 

## Bugs and requests
Please use the [issue tab of the github page](https://github.com/ssciwr/iSparrow/issues) to report any bugs or feature requests. 

## Contributions 
Feel free to contribute tot this project by opening a pull request [here](https://github.com/ssciwr/iSparrow/pulls). 