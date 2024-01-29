import yaml
import numpy as np
import tifffile as tiff
from tqdm import tqdm
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import interp1d
import sys
import os
sys.path.insert(0,"/Users/louaness/Documents/cohesin_residence_time/ipa/utils/")
from interactive_analysis_utils import zoomed_image, compute_lab, overlap, _create_logger
import questionary

import pandas as pd


def main(im_path:str,FRAP_frame:str,size_of_bbox_zoom:int,
         frame_actualization:int,frame_pre_bleach:list,
         radius_unbleach_spot:int,radius_bleach_spot:int,
         interpolation_values:list,save_path:str,name_of_experiment:str) -> None:
    """
    Run the analysis pipeline.
    
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

    ## Setting up the logger

    logger = _create_logger(name="interactive analysis")

    logger.info(f"Processing: {im_path} \n")
    
    logger.info(f"Output directory: {save_path}\n")

    logger.info(f"Name of experiment: {name_of_experiment}\n")
    logger.info(f"FRAP frame: {FRAP_frame}\n")
    logger.info(f"Size of bbox zoom: {size_of_bbox_zoom}\n")
    logger.info(f"Frame actualization: {frame_actualization}\n")
    logger.info(f"Frame pre bleach: {frame_pre_bleach}\n")
    logger.info(f"Radius unbleach spot: {radius_unbleach_spot}\n")
    logger.info(f"Radius bleach spot: {radius_bleach_spot}\n")
    logger.info(f"Interpolation values: {interpolation_values}\n")

    logger.info(f"Loading image: {im_path}\n")

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

    logger.info(f"Image shape: {im.shape}\n")

    # Measure the bleaching of the fluorophore

    print('Start by measuring fluorophore bleaching')

    fig,ax = plt.subplots(1,3,figsize=(20,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[2].imshow(im[-1,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')
    ax[2].set_title('Last frame')

    for a in ax:
        a.axis('off')

    fig.tight_layout()

    if plt.waitforbuttonpress():
        plt.close()

    ## Measure the bleaching of the fluorophore
    number = questionary.path('How many cells do you want to analyze?').ask()

    coords_fluo_bleach_total = plt.ginput(int(number))

    intensity_bleach = np.zeros((int(number),np.shape(im)[0]))
    labels = compute_lab(im) # perform the otsu segmentation on the image
    size = size_of_bbox_zoom 

    for index,coords_fluo_bleach in enumerate(coords_fluo_bleach_total):

        logger.info(f"Coordinates of fluorophore bleaching {index}: {coords_fluo_bleach}\n")

        center = [int(x) for x in list(coords_fluo_bleach)]

        labs = overlap(labels,center) # track the selected cell in the image and return the label of the cell

        labels_final = labels.copy()

        for ind,l in enumerate(labs):
            labels_final[ind+1,...] = np.where(labels_final[ind+1,...] == l,1,0) # create a mask of the selected cell in the image

        label_number = labels_final[0,...][int(center[1]), int(center[0])]
        labels_final[0,...] = np.where(labels_final[0,...] == label_number,1,0) # add the first frame

        int_im = im*(labels_final==1.) # mask the intensity image with the selected cell

        ## DEBUG

        #tiff.imwrite(save_path.split('/')[-1]+'_int_im.tif',int_im)
        
        #np.save(save_path.split('/')[-1]+'_int_im.npy',int_im)

        ## END DEBUG

        for frame in tqdm(range(np.shape(int_im)[0])):
            intensity_bleach[index][frame] = np.mean(int_im[frame,...][int_im[frame,...]>0]) #compute the mean intensity of the masked image without the background (0)

    logger.info(f'mean unfrapped cell intensity: {intensity_bleach}\n')

    ## DEBUG
    #np.save(save_path.split('/')[-1]+'_intensity_bleach.npy',intensity_bleach)
    ## END DEBUG

    # start analyzing the FRAPed cells
    number = questionary.path('How many cells (ROIs) do you want to analyze?').ask()

    logger.info(f"Number of cells processed: {number}\n")

    fig,ax = plt.subplots(1,2,figsize=(15,5))
    ax[0].imshow(im[0,...],cmap='viridis')
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis')
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('FRAP image')

    for a in ax:
        a.axis('off')
    
    fig.tight_layout()

    coords = plt.ginput(int(number))

    if plt.waitforbuttonpress():
        plt.close()

    logger.info(f"Coordinates of cells analyzed: {coords}\n")
    print('You entered %s' % coords)

    # lists that will contain the iFRAP curves, the raw data and the interpolated data
    ifrap = []
    df_list_raw = []
    df_list_interp = []

    _,ax = plt.subplots(1,3,figsize=(15,5))
    # loop over the selected cells
    for index,coord in enumerate(coords):

        c = [int(x) for x in list(coord)]
        center = c 
        size = size_of_bbox_zoom 

        zoomed_im = zoomed_image(logger,im, center, size) 
        # crop the image around the selected cell

        im_r = zoomed_im

        logger.info(f"The shape of the image analyzed centered at {c} is {im_r.shape}\n")

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

        logger.info(f'The image was actualized every {frame_actualization} frames\n')

        ## add the circles to the image (in the first frame to be able to actualie them after every frame)
        c_plot = patches.Circle((0, 0), 0, edgecolor='red', facecolor='none')
        c_plot_b = patches.Circle((0, 0), 0, edgecolor='blue', facecolor='none')
        c_plot_bck = patches.Circle((0, 0), 0, edgecolor='green', facecolor='none')

        c_plot_2 = patches.Circle((0, 0), 0, edgecolor='red', facecolor='none')
        c_plot_b_2 = patches.Circle((0, 0), 0, edgecolor='blue', facecolor='none')
        c_plot_bck_2 = patches.Circle((0, 0), 0, edgecolor='green', facecolor='none')

        ax[1].add_patch(c_plot)
        ax[1].add_patch(c_plot_b)
        ax[1].add_patch(c_plot_bck)
        ax[2].add_patch(c_plot_2)
        ax[2].add_patch(c_plot_b_2)
        ax[2].add_patch(c_plot_bck_2)

        previous_frame = 0 # initialize the previous frame to 0 to be able to plot both the actual and previous frame

        for i in range(0,im_r.shape[0]):
            if counter % frame_actualization == 0 or i in frame_pre_bleach:
                counter += 1
                # Display the image
                ax[0].imshow(im_r[i,...], cmap='viridis')                
                ax[0].set_title(f'Frame {i}')

                # before the FRAP frame, display the frame after frap to be able to see where the unbleached spot is

                if i <= FRAP_frame:
                    ax[1].imshow(im_r[FRAP_frame,...], cmap='viridis',zorder=0)
                    ax[1].set_title(f'Frame {FRAP_frame} with detections at frame {previous_frame}')
                else:
                    ax[1].imshow(im_r[i,...], cmap='viridis',zorder=0)
                    ax[1].set_title(f'Frame {i} with detections at frame {previous_frame}')

                if i > 0:
                    ax[2].imshow(im_r[previous_frame,...], cmap='viridis',zorder=0)
                    ax[2].set_title(f'Frame {previous_frame} with detections at frame {previous_frame}')
                else:
                    ax[2].imshow(im_r[i,...], cmap='viridis',zorder=0)
                    ax[2].set_title(f'Frame {i}')
                
                previous_frame = i
                radius = radius_unbleach_spot
                radius_b = radius_bleach_spot
                # Create a circle patch
                a = plt.ginput(3) # select the unbleached spot, the bleached spot and the background
                x,y = a[0]
                x_b,y_b = a[1]
                x_bck,y_bck = a[2]
                
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

                # Actualize the coordinate of the circles to be able to plot them in the next frame
                c_plot.center = x, y
                c_plot.radius = radius
                c_plot_b.center = x_b, y_b
                c_plot_b.radius = radius_b
                c_plot_bck.center = x_bck, y_bck
                c_plot_bck.radius = radius_b

                c_plot_2.center = x, y
                c_plot_2.radius = radius
                c_plot_b_2.center = x_b, y_b
                c_plot_b_2.radius = radius_b
                c_plot_bck_2.center = x_bck, y_bck
                c_plot_bck_2.radius = radius_b

                # compute the mean intensity of the pixels inside the circles
                mean_list_unbleached.append(np.mean(pixels_in_unbleached))
                mean_list_bleached.append(np.mean(pixels_in_bleached))
                mean_list_background.append(np.mean(pixels_in_background))
                frames.append(i)

                for i in ax:
                    i.axis('off')

                plt.tight_layout()
            else:
                counter += 1
                continue
            
        if plt.waitforbuttonpress():
            plt.close()

        logger.info(f"Mean intensity of unbleached spot: {mean_list_unbleached}\n")
        logger.info(f"Mean intensity of bleached spot: {mean_list_bleached}\n")

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

        # Compute the iFRAP curve
        iFRAP = (interpolated_values_unbleached-interpolated_values_bleached)/(np.mean(intensity_bleach,axis=0) - interpolated_values_background) #compute the iFRAP curve as defined by Gabriele et al. science 2022

        ifrap.append(iFRAP)

        # put all the data in a dataframe

        df = pd.DataFrame([mean_list_background,mean_list_bleached,mean_list_unbleached],
                          index=['mean_list_background','mean_list_bleached','mean_list_unbleached'])
        df = df.T
        df['nucleus'] = [index]*len(df)
        df['unfrap_cell'] = [np.mean(intensity_bleach,axis=0)[fra] for fra in frames]

        df_list_raw.append(df)

        df = pd.DataFrame([iFRAP,interpolated_values_background,interpolated_values_bleached,interpolated_values_unbleached],
                          index=['iFRAP','interpolated_values_background','interpolated_values_bleached','interpolated_values_unbleached'])
        
        df = df.T
        df['nucleus'] = [index]*len(df)
        df['unfrap_cell'] = np.mean(intensity_bleach,axis=0)
        df_list_interp.append(df)

        # remove the circles between each analyzed cells

        c_plot.remove()
        c_plot_b.remove()
        c_plot_2.remove()
        c_plot_b_2.remove()

    
    # save the data
    np.save(save_path.split('/')[-1]+'.npy',ifrap)
    df_list_raw = pd.concat(df_list_raw)
    df_list_interp = pd.concat(df_list_interp)
    df_list_interp.rename(columns={'Unnamed: 0':'time'},inplace=True)
    df_list_raw.rename(columns={'Unnamed: 0':'time'},inplace=True)
    df_list_raw.to_csv(save_path.split('/')[-1]+'_raw.csv')
    df_list_interp.to_csv(save_path.split('/')[-1]+'_interp.csv')

    logger.info(f"Created the output file {save_path.split('/')[-1]}.npy\n")
    logger.info("Done!")


# Execute the file
    
path = os.getcwd()

if __name__ == "__main__":

    from build_interactive_config import CONFIG_NAME

    with open(path+'/'+CONFIG_NAME, "r") as f:
        config = yaml.safe_load(f)

    main(**config)
