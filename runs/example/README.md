# Example
<!-- start processing steps summary -->
The image processing and analysis of this project is organized in three steps:
1. building the config file with the different parameters unique for the image,
2. running the GUI analysis for selecting and updating ROIs,
3. post processing of the data to extract the iFRAP curves.

The required scripts are organized in the `ipa` directory. Each step follows the pattern of building a config file and then running the respective script.
Each run should have its respective run-directory. Inside the run-directory the config files and log files are stored with time stamps for the different runs. The log files also contain every parameters in the corresponding config file, however, only one config file per run is kept (the latest).
<!-- end processing steps summary -->

Before running the scripts you must [activate your environment](../../infrastructure/apps/README.md).

<!-- start instructions -->
## Build config file
```{note}
The scripts write the config file into a new directory in /runs/ the folder is named after the first input given when building the config file. In this example it is assumed that you are in the home directory of the repository.
```
Build the config file:<br>
    `python ipa/build_interactive_config.py`


## Run the analysis
```{note}
The scripts write the log files into the current working directory. In this example it is assumed that you are in `runs/name of your experiment/`
```
Run the analysis:<br>
    `python ../../ipa/run_analysis.py`

<!-- end instructions -->
