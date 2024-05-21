[![tests](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/ssciwr/iSparrow/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/ssciwr/iSparrow/graph/badge.svg?token=FwyE0PNiOk)](https://codecov.io/gh/ssciwr/iSparrow)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ssciwr_iSparrow&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=ssciwr_iSparrow)
[![Supported OS: Linux | macOS | Windows](https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20Windows-green.svg)](https://www.linux.org/)
[![Documentation](https://readthedocs.org/projects/isparrow/badge/?version=latest)](https://isparrow.readthedocs.io/en/latest/?badge=latest)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Faunanet-lab
## What is it? 
`faunanet-lab` is an extension of [*Birdnet-Analyzer*](https://github.com/kahst/BirdNET-Analyzer), and uses [*birdnetlib*](https://github.com/joeweiss/birdnetlib) as its basis. 
`faunanet-lab` was developed with the goal to provide a platform for bioacoustics research projects, started at the Interdisciplinary center for scientific computing at the University of Heidelberg. 

## Features
Using the birdnetv2.4 model by default, `faunanet-lab` provides three core features: 

- Easily and arbitrarily exchange the underlying maching learning model for bioacoustics.
- Easy configuration using YAML files which are stored alongside the analysis results. 
- Integrated, extendible REPL with which to interact with which to interact with a running instance.

The main element of `faunanet-lab` is a 'watcher' system that continuously monitors a folder for incoming data files and allows for on-the-fly model- or parameter-change via the REPL. It can also be used as a library in your python project.
By extending elements of bridnetlib rather, `faunanet-lab` conserves the latter's capabilities while still adding its own functionality on top of it. 

## Getting started 
Please refer to the 'Getting faunanet-lab up and running' section in the documentation for an introduction. 

## Bugs, issues and feature requests
Please use the [issue tab of the github page](https://github.com/ssciwr/iSparrow/issues) to report any bugs or feature requests. 

## Contributions 
Feel free to contribute tot this project by opening a pull request [here](https://github.com/ssciwr/iSparrow/pulls). 