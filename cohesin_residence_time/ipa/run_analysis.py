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
    Apply preprocessing step to raw data.

    Parameters
    ----------
    raw_data_dir
        Directory containing all raw data.
    output_dir
        Directory where the preprocessed data is saved.

    """
    logger = _create_logger(name="interactive analysis")

    logger.info(f"Processing: {im_path}")
    logger.info(f"Output directory: {save_path}")

    im = tiff.imread(im_path)

    plt.waitforbuttonpress()
    fig,ax = plt.subplots(1,2,figsize=(15,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')

    if plt.waitforbuttonpress():
        plt.close()

    plt.waitforbuttonpress()
    number = questionary.path('How many cells (ROIs) do you want to analyze?').ask()

    logger.info(f"Number of cells processed: {number}")

    fig,ax = plt.subplots(1,2,figsize=(15,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')

    coords = plt.ginput(int(number))

    if plt.waitforbuttonpress():
        plt.close()

    logger.info(f"Coordinates of cells analyzed: {coords}")
    print('You entered %s' % coords)

    im_unfrap = im[:,152:195,87:132]
    labels_final = compute_lab(im_unfrap)

    int_im = im_unfrap*(labels_final==1.) #mask the image with the label

    intensity_bleach = []
    for frame in tqdm(range(np.shape(int_im)[0])):
        intensity_bleach.append(np.mean(int_im[frame,...][int_im[frame,...]>0])) #compute the mean intensity of the masked image without the background (0)

    ifrap = []
    for coord in coords:
        c = [int(x) for x in list(coord)]
        # Use the function
        center = c # Replace with the actual coordinates
        size = size_of_bbox_zoom  # Replace with the actual size


        zoomed_im = zoomed_image(im, center, size)

        im_r = zoomed_im

        labels_final = compute_lab(im_r)

        background = im_r*(labels_final==0.)

        int_background = np.zeros(np.shape(im_r)[0])

        for frame in tqdm(range(np.shape(im_r)[0])):
            int_background[frame] = np.mean(background[frame,...][background[frame,...]>0])

        mean_list_bleached = []
        mean_list_unbleached = []

        frames = []
        # Get the shape of your image
        height, width = im_r[0,...].shape

        counter = 1
        plt.waitforbuttonpress()

        print('Click on the center of the unbleached spot, then on the bleached spot')
        print('Press any key to end the selection')

        logger.info(f'The image was actualized every {frame_actualization} frames')
        for i in range(0,im_r.shape[0]):
            if counter % frame_actualization == 0 or i in frame_pre_bleach:
                counter += 1

                # Display the image
                plt.subplot(1,2,1)
                plt.imshow(im_r[i,...], cmap='viridis')
                plt.title(f'Frame {i}')

                radius = radius_unbleach_spot
                radius_b = radius_bleach_spot
                # Create a circle patch
                a = plt.ginput(2)
                x,y = a[0]
                x_b,y_b = a[1]

                circle = patches.Circle((x, y), radius, edgecolor='r', facecolor='none')
                circle_b = patches.Circle((x_b, y_b), radius, edgecolor='green', facecolor='none')
                # Get the current axes, and add the circle to them
                ax = plt.gca()

                circle_stored = ax.add_patch(circle)
                circle_stored_b = ax.add_patch(circle_b)

                circle_stored.remove()
                circle_stored_b.remove()
                
                # Create an array of indices
                y_indices, x_indices = np.ogrid[:height, :width]
                y_indices_b, x_indices_b = np.ogrid[:height, :width]

                # Create a binary mask where the pixels inside the circle are True
                mask = (x_indices - x)**2 + (y_indices - y)**2 <= radius**2
                maks_bck = (x_indices_b - x_b)**2 + (y_indices_b - y_b)**2 <= radius_b**2

                # Use the mask to index into your image and extract the pixel values
                pixels_in_circle = im_r[i,...][mask]
                pixels_in_bck = im_r[i,...][maks_bck]
                plt.subplot(1,2,2)
                plt.imshow(mask, cmap='viridis')
                plt.imshow(maks_bck, cmap='viridis',alpha=0.5)
                plt.title(f'Mean intensity in this patch {np.mean(pixels_in_circle):.2f}, \n background {np.mean(pixels_in_bck):.2f}')

                mean_list_unbleached.append(np.mean(pixels_in_circle))
                mean_list_bleached.append(np.mean(pixels_in_bck))
                frames.append(i)
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

        # New x values for interpolation
        x_new = np.arange(0, 250)

        # Interpolate the data at new x values
        interpolated_values_unbleached = f_unbleach(x_new)
        interpolated_values_bleached = f_bleach(x_new)

        iFRAP = (interpolated_values_unbleached-interpolated_values_bleached)/(intensity_bleach - int_background) #compute the iFRAP curve as defined by Gabriele et al. science 2022

        ifrap.append(iFRAP)
        frames_m = [x*0.5 for x in range(len(iFRAP))]  

        plt.figure(figsize=(15,5))
        plt.subplot(1,2,1)
        plt.plot(interpolated_values_unbleached[FRAP_frame+1],marker='.',label='mean intensity unbleached')
        plt.plot(interpolated_values_bleached[FRAP_frame+1],marker='.',label='mean intensity bleached')
        plt.scatter(frames[FRAP_frame+1],mean_list_unbleached[FRAP_frame+1],marker='o',label='points unbleached')
        plt.scatter(frames[FRAP_frame+1],mean_list_bleached[FRAP_frame+1],marker='o',label='points bleached')
        plt.plot(intensity_bleach[FRAP_frame+1],marker='.',label='bleach of fluorophore')
        plt.plot(int_background[FRAP_frame+1],marker='.',label='background')

        plt.legend()
        plt.subplot(1,2,2)
        plt.plot(frames_m[FRAP_frame+1],iFRAP[FRAP_frame+1],marker='.',label='iFRAP')
        plt.legend()
        plt.show()

    np.save(save_path+'.npy',ifrap)
    logger.info(f'Created the output file {save_path}.npy')
    logger.info("Done!")

path = os.getcwd()

if __name__ == "__main__":

    from build_interactive_config import CONFIG_NAME

    with open(path+'/'+CONFIG_NAME, "r") as f:
        config = yaml.safe_load(f)

    main(**config)
