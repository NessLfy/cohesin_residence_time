# Processing Steps
```{include} ../../runs/example/README.md
:start-after: <!-- start processing steps summary -->
:end-before: <!-- end processing steps summary -->
```

## Build the config file

The building of the config file is necessary to be able to perform the analysis through the GUI.

Once executed the program will ask for the following questions:
- Name of experiment:
    - This parameter will indicate the name of the folder created in the runs folder. If no value is inputed (or return is pressed), the folder created will be named test.

- FRAP frame:
    - This parameter corresponds to the number of the frame in which the FRAP occured (starting to count at 1). Although the frame of the FRAP is not recorded on the microscope, this parameter is useful to display the pre/post FRAP frames when selecting the ROIs. If no parameter is inputed the default value will be 4.

- Path to image:
    - This parameter corresponds to the path to the image to process (absolute). If no value is inputed the default is /Volumes/tungsten/scratch/ggiorget/nessim/microscopy_data/FRAP_Rad21_halo/20231124_FRAP_WAPL_AID_NIPBL_FKBP/20231124_FRAP_NIPBL_FKBP_Rad21_Halo_561_1_conf561Triple-LP-FRAP.ome.tf2

- Size of bbox zoom:
    - This parameter corresponds to the size of the bounding box for zooming in on the image around the  cell of interest. If no value is inputed, the default size will be 100.

- Frame actualization:
    - This parameter corresponds to the frequency at which the frame updates. If no value is inputed, the default frequency will be 25 frames.

- Frame pre bleach:
    - This parameter corresponds to the frames before the bleaching event. If no value is inputed, the default frames will be [0,1,2,3,5,249]. Note the 249 in the default that corresponds to the last frame in my case. This is to also sample the last point.

- Radius unbleach spot:
    - This parameter corresponds to the radius of the unbleached spot in the image. If no value is inputed, the default radius will be 5. This radius corresponds to the radius of a circle in which the (average) intensity will be read.

- Radius bleach spot:
    - This parameter corresponds to the radius of the bleached spot in the image. If no value is inputed, the default radius will be 7.

- Interpolation values:
    - This parameter corresponds to the frames at which the image will be interpolated i.e. the frames at which the intensities were samples. If no value is inputed, the default frames will be [0,1,2,3,5, 24, 49, 74, 99, 124, 149, 174, 199, 224, 249].

- Save path:
    - This parameter corresponds to the path where the results will be saved. If no value is inputed, the default path will be '/Users/louaness/Documents/cohesin_residence_time/cohesin_residence_time/runs/'. I recommend to input the path to the /run folder in your folder structure.

## Running the GUI

1. Step 1: Parseyaml config file

The function starts by opening and parsing the yaml file for the parameters used in the analysis. 

2. Step 2: Set up logging
The function then sets up logging using the logging module. 
This allows for tracking the progress of the analysis and debugging if necessary.

3. Step 3: Load data
The function loads the data from the specified file path. 
The data is expected to be in a specific format for the analysis to work correctly i.e. that it can be read by the function imread of the python module [tifffile](https://github.com/cgohlke/tifffile)

4. Step 4: Preprocess unfrapped cells
The program will ask for a number and to click on n cells to analyze. These cells should not have been FRAP. The cells will be segmented using Otsu's method and tracked using IoU mask-overlapping. For better efficiency please select cells that are not too close together or think about implementing another type of segmentation.

5. Step 5: Select rois and measure intensity

(in-progress)

Please note that this is a general documentation for more detailed information see the actual function in ipa/run_analysis.py

## Extracting the iFRAP curve

(in-progress)
