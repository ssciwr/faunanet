# Faunanet
## What is it? 
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
Please use the [issue tab of the github page](https://github.com/ssciwr/faunanet/issues) to report any bugs or feature requests. 

## Contributions 
Feel free to contribute to this project by opening a pull request [here](https://github.com/ssciwr/faunanet/pulls). 
