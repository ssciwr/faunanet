# Basic design of faunanet-lab
Because the rest of the documentation is relatvely technical, it makes sense to first give an overview over the basic ideas behind `faunanet-lab`'s design.
`faunanet-lab` has been developed in a scientific context, and thus it strive to by default produce reproducible and well documented results.

## Analysis in batches
Each time `faunanet-lab` is started, a new folder is created in the configured output folder, which uses the current date and time as folder name, according to the format `yymmdd_hhMMss`. In this folder, all analysis results will be written until the current watcher process stops again. When it is started up again, a new such folder is created. Each 'run' of `faunanet-lab` hence corresponds to a batch of input files which area analyzed with a particular machine learning model configured with a particular set of parameters. 

`faunanet-lab` always bundles the configuration file that contains all its parameters together with the results and stores them together in the same folder. 
Every time the machine learning model is exchanged or the `faunanet-lab` process is restarted, a new batch will be created in a new folder. 
Additionally, methods are provided that can be used to ensure data consistency even when the watcher process is shut down or crashes unexpectedly, such that analysis data is not lost. 
After a number of restarts and/or model exchanges, you will end up with a folder structure like this: 
```
faunanet-lab_output
  240510_150322 # batch 1
    results_file1.csv
    results_file2.csv
    ...
    results_fileM.csv 
    config.yml # configuration with which the results where created.
    missings.txt # list of files that have been reanalyzed to ensure data consistency. Call `clean_up` to do this explicitly.
    
  240511_080343 # batch 2
    results_file1.csv
    results_file2.csv
    ...
    results_fileN.csv 
    config.yml
    missings.txt 
    
  240513_183323 # batch 3
    results_file1.csv
    results_file2.csv
    ...
    results_fileL.csv 
    config.yml 
    missings.txt 
```

## Separate code and parameterization 
All parameterization of any `faunanet-lab` functionality happens via `.yml` files. This serves two purposes:  
- It centralizes where parameters are defined and clearly separates them from the code itself, thus providing a cleaner interface. 
- It allows to bundle results with the parameters with which they were obtained (see above) and thus improves reproducibility. These advantages extend to all aspects of package development and usage, as defining and paramterizing software tests profits as much from this approach as running `faunanet-lab` with different machine learning models.

`faunanet-lab` uses configuration files both for its own setup and for running maching learning models to analyze audio data. 

## Defined interface for customization
`faunanet-lab` allows the user to run their own machine learning models for audio classification by providing interfaces for how to call the model (the `ModelBase` class) and for how preprocessing the data (the `PreprocessorBase` class). Leveraging [birdnetlib](https://github.com/joeweiss/birdnetlib) these interface allow for easy extendability. Finally, `faunanetlib` provides a defined structure for the configuration files (see {doc}`using_configuration_files`) with which custom models can be controlled.

```{important}
Currently it is not enforced in the code that the config file layout adheres to the defined interface or that the Model and Preprocessor implementations provided with a model actually derive from `ModelBase` or `PreprocessorBase`. Failure to adhere to the defined interfaces is currently undefined and will generally lead to fatal errors that lead to a crash. 
```