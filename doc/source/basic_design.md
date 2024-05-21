# Basic design of Faunanetlab
`Faunanetlab` has been developed in a scientific context, and thus strives to adhere to scientific principles in its implementation. 

## Analysis in batches
Each time `Faunanetlab` is started, a new folder is created in the configured output folder, which uses the current date and time as folder name, according to the format `yymmdd_hhMMss`. In this folder, all analysis results will be written that are created until the current watcher process stops. When it is started up again, a new such folder is created. Each 'run' of `Faunanetlab` hence corresponds to a batch of input files which area analyzed with a particular machine learning model configured with a particular set of parameters. `Faunanetlab` always bundles the configuration file that contains the name of the used machine learning model and the parameters used for running the model and prepocessing the data together with the results and stores them in all together in the same folder. 
Each csv-file that contains analysis results contains the input filename in its filename. 
In this way, it is always documented how certain results where obtained and from where.

Every time the machine learning model is exchanged or the `Faunanetlab` process is restarted, a new batch will be created in a new folder. 
Additionally, methods are provided that ensure data consistency even when the watcher process is shut down or crashes unexpectedly, such that analysis data is not lost. 
After a number of restarts and/or model exchanges, you will end up with a folder structure like this: 
```
Faunanetlab_output
  240510_150322 # batch 1
    results_file1.csv
    results_file2.csv
    ...
    results_fileM.csv 
    config.yml # configuration with which the results where created.
    missings.txt # list of files that have been reanalyzed to ensure data consistency
    
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
All parameterization of any `Faunanetlab` functionality happens via `.yml` files. This choice serves two purposes:  
First, it centralizes where parameters are defined and clearly separates it from the code itself, thus providing a cleaner interface. Second, it allows to bundle results with the parameters with which they were obtained (see above) and thus improves reproducibility. These advantages extend to all aspects of package development and usage, as defining and paramterizing software tests profits as much from this approach as running `Faunanetlab` with different machine learning models in a scientific setting or wanting to change the hardware of your homemade bioacoustic lab that records the birds in your garden.

`Faunanetlab` uses configuration files both for its own setup and for the running of maching learning models to analyze audio data.