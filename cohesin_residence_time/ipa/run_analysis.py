"""
run_preprocessing.py
====================

This script expects preprocessing_config.yaml to be present in the current
working directory.
"""

import yaml
from datetime import datetime
import logging
import numpy as np
import tifffile as tiff
from tqdm import tqdm
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import interp1d
from utils.interactive_analysis_utils import zoomed_image, compute_lab
import questionary
import os
import pandas as pd

def _create_logger(name: str) -> logging.Logger:
    """
    Create logger which logs to <timestamp>-<name>.log inside the current
    working directory.

    Parameters
    ----------
    name
        Name of the logger instance.
    """
    logger = logging.Logger(name.capitalize())
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    handler = logging.FileHandler(f"{now}-{name}.log")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def main(im_path:str,FRAP_frame:str,size_of_bbox_zoom:int,
         frame_actualization:int,frame_pre_bleach:list,
         radius_unbleach_spot:int,radius_bleach_spot:int,
         interpolation_values:list,save_path:str,name_of_experiment:str) -> None:
    """
    Run the preprocessing pipeline.
    
    Parameters
    ----------
    im_path, str: path to the image
    FRAP_frame, int: frame of the FRAP
    size_of_bbox_zoom, int: size of the zoomed image
    frame_actualization, int: frame actualization
    frame_pre_bleach, list: list of frames before the FRAP
    radius_unbleach_spot, int: radius of the unbleached spot
    radius_bleach_spot, int: radius of the bleached spot
    interpolation_values, list: list of interpolation values
    save_path, str: path to save the results
    name_of_experiment, str: name of the experiment
    """
    logger = _create_logger(name="interactive analysis")

    logger.info(f"Processing: {im_path}")
    logger.info(f"Output directory: {save_path}")

    logger.info(f"Name of experiment: {name_of_experiment}")
    logger.info(f"FRAP frame: {FRAP_frame}")
    logger.info(f"Size of bbox zoom: {size_of_bbox_zoom}")
    logger.info(f"Frame actualization: {frame_actualization}")
    logger.info(f"Frame pre bleach: {frame_pre_bleach}")
    logger.info(f"Radius unbleach spot: {radius_unbleach_spot}")
    logger.info(f"Radius bleach spot: {radius_bleach_spot}")
    logger.info(f"Interpolation values: {interpolation_values}")

    logger.info(f"Loading image: {im_path}")

    # Load the image
    im = tiff.imread(im_path)

    # Display the image

    plt.waitforbuttonpress()
    _,ax = plt.subplots(1,2,figsize=(15,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')

    for a in ax:
        a.axis('off')

    if plt.waitforbuttonpress():
        plt.close()

    plt.waitforbuttonpress()

    logger.info(f"Image shape: {im.shape}")

    # Measure the bleaching of the fluorophore

    print('Start by measuring fluorophore bleaching')

    _,ax = plt.subplots(1,3,figsize=(20,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[2].imshow(im[-1,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')
    ax[2].set_title('Last frame')

    for a in ax:
        a.axis('off')

    plt.tight_layout()
    
    coords_fluo_bleach = plt.ginput(1)[0]

    if plt.waitforbuttonpress():
        plt.close()
    
    logger.info(f"Coordinates of fluorophore bleaching: {coords_fluo_bleach}")

    center = [int(x) for x in list(coords_fluo_bleach)]
    
    size = size_of_bbox_zoom  # Replace with the actual size

    zoomed_im = zoomed_image(im, center, size)

    labels = compute_lab(zoomed_im)

    int_im = zoomed_im*(labels==1.)

    intensity_bleach = []
    for frame in tqdm(range(np.shape(zoomed_im)[0])):
        intensity_bleach.append(np.mean(int_im[frame,...][int_im[frame,...]>0])) #compute the mean intensity of the masked image without the background (0)

    logger.info(f'unfrapped cell intensity: {intensity_bleach}')

    # start analyzing the FRAPed cells

    number = questionary.path('How many cells (ROIs) do you want to analyze?').ask()

    logger.info(f"Number of cells processed: {number}")

    _,ax = plt.subplots(1,2,figsize=(15,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')

    coords = plt.ginput(int(number))

    if plt.waitforbuttonpress():
        plt.close()

    logger.info(f"Coordinates of cells analyzed: {coords}")
    print('You entered %s' % coords)

    ifrap = []
    df_list_raw = []
    df_list_interp = []
    for index,coord in enumerate(coords):

        c = [int(x) for x in list(coord)]
        center = c 
        size = size_of_bbox_zoom 

        zoomed_im = zoomed_image(im, center, size)

        im_r = zoomed_im

        mean_list_bleached = []
        mean_list_unbleached = []
        mean_list_background = []

        frames = []
        # Get the shape of your image
        height, width = im_r[0,...].shape

        counter = 1
        plt.waitforbuttonpress()

        print('Click on the center of the unbleached spot then on the bleached spot finally on the background of the crop')
        print('Press any key to end the selection')

        logger.info(f'The image was actualized every {frame_actualization} frames')
        for i in range(0,im_r.shape[0]):
            if counter % frame_actualization == 0 or i in frame_pre_bleach:
                counter += 1
                _,ax = plt.subplots(1,2,figsize=(15,5))
                # Display the image
                ax[0].imshow(im_r[i,...], cmap='viridis')
                ax[0].set_title(f'Frame {i}')
                ax[1].imshow(im_r[FRAP_frame,...], cmap='viridis')
                ax[1].set_title(f'Frame {FRAP_frame}')

                radius = radius_unbleach_spot
                radius_b = radius_bleach_spot
                # Create a circle patch
                a = plt.ginput(3) #click on the center of the unbleached spot, then on the bleached spot then on the background of the crop
                x,y = a[0]
                x_b,y_b = a[1]
                x_bck,y_bck = a[2]

                circle = patches.Circle((x, y), radius, edgecolor='r', facecolor='none')
                circle_b = patches.Circle((x_b, y_b), radius, edgecolor='green', facecolor='none')
                circle_bck = patches.Circle((x_bck, y_bck), radius, edgecolor='blue', facecolor='none')
                # Get the current axes, and add the circle to them
                a = plt.gca()

                circle_stored = a.add_patch(circle)
                circle_stored_b = a.add_patch(circle_b)
                circle_stored_bck = a.add_patch(circle_bck)

                circle_stored.remove()
                circle_stored_b.remove()
                circle_stored_bck.remove()
                
                # Create an array of indices
                y_indices, x_indices = np.ogrid[:height, :width]
                y_indices_b, x_indices_b = np.ogrid[:height, :width]
                y_indices_bck, x_indices_bck = np.ogrid[:height, :width]

                # Create a binary mask where the pixels inside the circle are True
                mask_unbleached = (x_indices - x)**2 + (y_indices - y)**2 <= radius**2
                mask_bleached = (x_indices_b - x_b)**2 + (y_indices_b - y_b)**2 <= radius_b**2
                mask_background = (x_indices_bck - x_bck)**2 + (y_indices_bck - y_bck)**2 <= radius_b**2

                # Use the mask to index into your image and extract the pixel values
                pixels_in_unbleached = im_r[i,...][mask_unbleached]
                pixels_in_bleached = im_r[i,...][mask_bleached]
                pixels_in_background = im_r[i,...][mask_background]

                ax[1].imshow(mask_unbleached, cmap='viridis',interpolation=None)
                ax[1].imshow(mask_bleached, cmap='viridis',alpha=0.5,interpolation=None)
                ax[1].set_title(f'Mean intensity in this patch {np.mean(pixels_in_unbleached):.2f}, \n bleach {np.mean(pixels_in_bleached):.2f} \n background {np.mean(pixels_in_background):.2f}')

                mean_list_unbleached.append(np.mean(pixels_in_unbleached))
                mean_list_bleached.append(np.mean(pixels_in_bleached))
                mean_list_background.append(np.mean(pixels_in_background))
                frames.append(i)

                for i in ax:
                    i.axis('off')


            else:
                counter += 1
                continue

        if plt.waitforbuttonpress():
            plt.close()

        logger.info(f"Mean intensity of unbleached spot: {mean_list_unbleached}")
        logger.info(f"Mean intensity of bleached spot: {mean_list_bleached}")

        # Original x values
        x_values = np.array(interpolation_values)

        # Create interpolation function
        f_unbleach = interp1d(x_values, mean_list_unbleached, kind='linear')
        f_bleach = interp1d(x_values, mean_list_bleached, kind='linear')
        f_background = interp1d(x_values, mean_list_background, kind='linear')

        # New x values for interpolation
        x_new = np.arange(0, im.shape[0])

        # Interpolate the data at new x values
        interpolated_values_unbleached = f_unbleach(x_new)
        interpolated_values_bleached = f_bleach(x_new)
        interpolated_values_background = f_background(x_new)

        iFRAP = (interpolated_values_unbleached-interpolated_values_bleached)/(intensity_bleach - interpolated_values_background) #compute the iFRAP curve as defined by Gabriele et al. science 2022

        ifrap.append(iFRAP)

        df = pd.DataFrame([mean_list_background,mean_list_bleached,mean_list_unbleached],
                          index=['mean_list_background','mean_list_bleached','mean_list_unbleached'])
        df = df.T
        df['nucleus'] = [index]*len(df)
        df['unfrap_cell'] = intensity_bleach[frames]

        df_list_raw.append(df)

        df = pd.DataFrame([iFRAP,interpolated_values_background,interpolated_values_bleached,interpolated_values_unbleached],
                          index=['iFRAP','interpolated_values_background','interpolated_values_bleached','interpolated_values_unbleached'])
        
        df = df.T
        df['nucleus'] = [index]*len(df)
        df['unfrap_cell'] = intensity_bleach
        df_list_interp.append(df)

    np.save(save_path.split('/')[-1]+'.npy',ifrap)
    df_list_raw = pd.concat(df_list_raw)
    df_list_interp = pd.concat(df_list_interp)
    df_list_interp.rename(columns={'Unnamed: 0':'time'},inplace=True)
    df_list_raw.rename(columns={'Unnamed: 0':'time'},inplace=True)
    df_list_raw.to_csv(save_path.split('/')[-1]+'_raw.csv')
    df_list_interp.to_csv(save_path.split('/')[-1]+'_interp.csv')

    logger.info(f"Created the output file {save_path.split('/')[-1]}.npy")
    logger.info("Done!")

path = os.getcwd()

if __name__ == "__main__":

    from build_interactive_config import CONFIG_NAME

    with open(path+'/'+CONFIG_NAME, "r") as f:
        config = yaml.safe_load(f)

    main(**config)
