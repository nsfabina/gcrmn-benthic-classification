# gcrmn-benthic-classification

## Important note

This repository is no longer maintained. We created a new repository for the next version of this map, given the significant changes to input data, network architectures, and other components. Importantly, this also allows us to recover the first version of the map and introspect the code at the point in time at which it was generated.

## Creating a global reef map

The goal of this repository is to develop models that can generate a global reef map for applied uses. We use deep learning and creative data and modeling choices to mitigate non-representative training data, only three feature bands, lack of NIR and depth data, and single images per location, among other limitations. The code base has been built up iteratively, with new information and changing requirements, the need for efficiency in spinning up and applying models, accounting for varying levels of progress in jobs, etc. For example:  many models can be trained, validated, and summarized with a single command; jobs can be started and restarted without losing progress or interfering with concurrent jobs; global appications to terabytes of data can be done quickly by throwing more GPUs at the task.

## Data management via `data_acquisition` and `data_cleaning` modules

The `data_acquistion` module downloads training and calval data from various locations. The `data_cleaning` module formats and cleans the data for use in downstream models. The nature of the data and models and the project requirements have changed over time, so all scripts are relatively specific, each performing usually only one or two tasks. It would be difficult to modify the data pipeline if the scripts were less modular. Due to the amount of data involved, it's often necessary to assume that new data will be processed and avoid reprocessing existing files, or to parallelize scripts for remote computing resources.

## Model training via `config` and `model_training` modules

The `config` module generates data and model configs compatible with the [bfg-nets package](https://pgbrodrick.github.io/bfg-nets/) that Phil Brodrick and I have developed. The configs specify data characteristics like where the feature and response files are located, how many samples should be generated, and how to scale and format the built data. The configs also specify model characteristics such as what type of network architecture to use, how to create the network architecture, and how to train the model. The `model_training` module uses these configs to build data and train models, using scripts to handle how to create and run jobs on the SLURM system.

## Model validation via `application_calval` module

The `application_calval` module uses trained models to generate maps at calval locations, and generates statistics and reports to quantify the performance of each model. Additional reports can be generated to compare models to one another and to various baseline maps. 

## Model validation via `application_global` module

Select models are applied to global imagery to generate global reef maps. Like other modules, the code is written in such a way that arbitrary numbers of jobs can be working on the global map concurrently, with code to lock an image when one job is working on it, to keep track of which images have valid reef area and which images have no reef area (i.e., all land or water), handle images that may be corrupt or missing, etc. A helpful script queries the GCS buckets to determine the application progress.
