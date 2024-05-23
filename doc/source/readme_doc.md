# About faunanet

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
Follow the instructions {doc}`getting_started` to install and use `faunanet-lab`.

## Contribution 
Issue- or bug reports and feature requests as well as code contributions are welcome here: https://github.com/ssciwr/iSparrow