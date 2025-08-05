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

1. Step 1: Parse yaml config file

The function starts by opening and parsing the yaml file for the parameters used in the analysis. 

2. Step 2: Set up logging
The function then sets up logging using the logging module. 
This allows for tracking the progress of the analysis and debugging if necessary.

3. Step 3: Load data
The function loads the data from the specified file path. 
The data is expected to be in a specific format for the analysis to work correctly i.e. that it can be read by the function imread of the python module [tifffile](https://github.com/cgohlke/tifffile)

4. Step 4: Preprocess unfrapped cells
The program will ask for a number and to click on n cells to analyze. These cells should not have been FRAP. The cells will be segmented using Otsu's method and tracked using IoU mask-overlapping. For better efficiency please select cells that are not too close together or think about implementing another type of segmentation.

5. Step 5: Select the background region

The program will ask to click on a region that doesn't contain any cells during the whole movie.

6. Step 6: Select rois and measure intensity

The user is asked to input the number of cells (ROIs) they want to analyze. The number of cells processed is then logged.

Loop over the selected cells: For each cell, the following steps are performed:

- The coordinates of the cell are converted to integers and stored in `c`.
- The `zoomed_image` function is called to crop the image around the selected cell. The cropped image is stored in `im_r`.
The shape of the cropped image is logged.
- Instructions are printed for the user to click on the center of the unbleached spot, then on the bleached spot, and finally on the background of the cropped image. The user is also instructed to press any key to end the selection. The frequency of image actualization is logged.

- Create patches for visualization: Three patches (circles) are created for each of the two axes (`ax[1] and ax[2]`). These patches will be used to visualize the unbleached spot, the bleached spot, and the background in the image.

- Initialize the previous frame: The variable previous_frame is initialized to 0. This variable will be used to keep track of the previous frame when looping through the frames of the image.

- Loop over the frames of the image: For each frame in the image, the following steps are performed:

    - If the current frame is a multiple of `frame_actualization` or is in `frame_pre_bleach`, the counter is incremented by 1.

    - The current frame is displayed on `ax[0]` with a title indicating the frame number.

    - If the current frame is less than or equal to the FRAP frame, the FRAP frame is displayed on `ax[1]` with a title indicating the FRAP frame and the previous frame. Otherwise, the current frame is displayed on `ax[1]` with a title indicating the current frame and the previous frame.

    - If the current frame is not the first frame, the previous frame is displayed on `ax[2]` with a title indicating the previous frame. Otherwise, the current frame is displayed on `ax[2]` with a title indicating the current frame.

    - Get the coordinates of the unbleached spot, the bleached spot, and the background: The `plt.ginput(3)` function is used to get the coordinates of three points in the image. These points represent the unbleached spot, the bleached spot, and the background.

    - Create arrays of indices: Arrays of indices are created for the height and width of the image. These arrays will be used to create binary masks for the unbleached spot, the bleached spot, and the background.

    - Create binary masks: Binary masks are created for the unbleached spot, the bleached spot, and the background. In these masks, the pixels inside the circles are True.

    - Extract pixel values: The binary masks are used to index into the image and extract the pixel values for the unbleached spot, the bleached spot, and the background.

    - Update the coordinates and radii of the circle patches: The coordinates and radii of the circle patches are updated to match the selected spots. This is done for both sets of patches (`c_plot` and `c_plot_2`).

    - Compute the mean intensity of the pixels inside the circles: The mean intensity of the pixels inside the circles is computed for the unbleached spot, the bleached spot, and the background. These mean intensities are appended to their respective lists.

    - Append the current frame number to the frames list: The current frame number is appended to the frames list.

- Finally:
    - Create interpolation functions: Interpolation functions are created for the mean intensity lists of the unbleached spot, the bleached spot, and the background. These functions will be used to interpolate the data at new x values.

    - Create new x values for interpolation: A new array of x values is created, ranging from 0 to the number of frames in the image.

    - Interpolate the data at new x values: The interpolation functions are used to interpolate the data at the new x values. The interpolated values are stored in `interpolated_values_unbleached`, `interpolated_values_bleached`, and `interpolated_values_background`.
    
    - Create dataframes for the raw and interpolated data: Two dataframes are created, one for the raw data and one for the interpolated data. The dataframes contain the mean intensity lists and the interpolated values for the unbleached spot, the bleached spot, and the background. They also contain a column for the nucleus index and a column for the mean intensity of the unfrapped cells.

    - Append the dataframes to the `df_list_raw` and `df_list_interp` lists: The created dataframes are appended to the df_list_raw and df_list_interp lists.

- Remove the circle patches from the axes: The circle patches that were added to the axes for visualization are removed. This is done for all six patches (`c_plot`, `c_plot_b`, `c_plot_2`, `c_plot_b_2`, `c_plot_bck`, and `c_plot_bck_2`).


**Please note that this is a general documentation for more detailed information see the actual function in `ipa/run_analysis.py`**
