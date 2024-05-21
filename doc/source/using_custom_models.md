# Using your own models with faunanet-lab
`faunanet-lab` allows you to run your own bioacoustic models for analysis. In order to do this, 
you have to do the following: 
- provide your model in the form of a `model.tflite` or `saved_model.pb` file such that it can 
be run with python tensorflow. Currently, only tensorflow models are supported. 
- provide a `labels.txt` file with the model file that contains the labels for the output of your model 
- write an implementation of the `faunanet-lab.ModelBase` class that uses your own model. `faunanet-lab` relies on this interface, so it **must not** be violated. The file must be called `model.py`.
- write an implementation of the `faunanet-lab.PreprocessorBase` class. This is used for preprocessing data in an appropriate way for your model. The same applies here as for the `ModelBase` class: `faunanet-lab` relies on the interface provided by this class, so it **must not**
be violated. The file must be called `preprocessor.py`.
- add a file `default.yml` that contains default values for all needed parameters for a `faunanet-lab` instance to run with your model. Have a look {doc}`using_configuration_files` for a minimal example to start from. The same as before holds: `faunanet-lab` relies on the general structure of this file and deviations from it will lead to errors. 
- package everything into a folder with an appropriate name that `faunanet-lab` should identify yoru model with. This folder must contain the above, but can contain arbitrary other data, too. The folder structure should look like this for example:
```
modelname 
- model.tflite
- labels.txt 
- model.py 
- preprocessor.py 
- default.yml 
- more data that may be needed...
- ...  
``` 
This folder then must be placed into the home folder of `faunanet-lab`, which by default is `~/faunanet-lab/models`. If you customized these locations upon install, put the folder into the respective directory where models are stored. 
After that, you can use the new model by supplying a config file with the `Analysis.modelname` node being replaced with the name of you model as described above.

Currently, there are no facilities in `faunanet-lab` to ,e.g., download models hosted on tensorflowhub or huggingface directly into `faunanet-lab`, so the procedure has to be done by hand. 
