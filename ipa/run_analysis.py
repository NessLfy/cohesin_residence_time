import yaml
import numpy as np
import tifffile as tiff
from tqdm import tqdm
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# from scipy.interpolate import interp1d
import sys
import os
sys.path.insert(0,"/Users/louaness/Documents/cohesin_residence_time/ipa/utils/")
from interactive_analysis_utils import zoomed_image, compute_lab, overlap, _create_logger # type: ignore
import questionary
import secrets

import pandas as pd
# DEBUG
# import cProfile

def main(im_path:str,FRAP_frame:str,size_of_bbox_zoom:int,
         frame_actualization:int,frame_pre_bleach:list,
         radius_unbleach_spot:int,radius_bleach_spot:int,
         save_path:str,name_of_experiment:str) -> None:
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

    logger.info(f"Loading image: {im_path}\n")

    # generate token to save the data

    token = secrets.token_hex(6) # 6 hex digits

    # Load the image

    try:
        im = tiff.imread(im_path)
    except Exception as e:
        logger.error(f"Error loading image: {e}\n, the path to the image is {im_path}\n")
        sys.exit(1)

    # Display the image

    plt.waitforbuttonpress()
    _,ax = plt.subplots(1,2,figsize=(15,5))
    vmin = np.min(im)
    vmax = np.quantile(im,0.999) # set the maximum value of displayed intensity to the 99.9th percentile (to avoid outliers)
    ax[0].imshow(im[0,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis',vmin=vmin,vmax=vmax)
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
    ax[0].imshow(im[0,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[2].imshow(im[-1,...],cmap='viridis',vmin=vmin,vmax=vmax)
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

    np.save(save_path.split('/')[-1]+f'_intensity_bleach_{token}.npy',intensity_bleach)

    # Analyze background level of the image

    print('Start by measuring background level, select a region without any cells')

    fig,ax = plt.subplots(1,3,figsize=(20,5))
    ax[0].imshow(im[0,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[2].imshow(im[-1,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[0].set_title('pre-FRAP image')
    ax[1].set_title('post-FRAP image')
    ax[2].set_title('Last frame')

    for a in ax:
        a.axis('off')

    fig.tight_layout()

    if plt.waitforbuttonpress() == False:
        coords = plt.ginput(1)
        plt.close()

    coords = [int(x) for x in coords[0]]

    radius_back  = 7

    height, width = im[0,...].shape

    x,y = coords

    y_indices, x_indices = np.ogrid[:height, :width]

    # Create a binary mask where the pixels inside the circle are True
    mask_back = (x_indices - x)**2 + (y_indices - y)**2 <= radius_back**2

    # Use the mask to index into the image and extract the pixel values (for every frame)
    pixels_back = [im[i,...][mask_back] for i in range(im.shape[0])]
    
    # save the mask with the background intensity

    np.save(save_path.split('/')[-1]+'_mask_back_'+token+'.npy',pixels_back)

    # start analyzing the FRAPed cells
    number = questionary.path('How many cells (ROIs) do you want to analyze?').ask()

    logger.info(f"Number of cells processed: {number}\n")

    fig,ax = plt.subplots(1,2,figsize=(15,5))
    ax[0].imshow(im[0,...],cmap='viridis',vmin=vmin,vmax=vmax)
    ax[1].imshow(im[FRAP_frame,...],cmap='viridis',vmin=vmin,vmax=vmax)
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
    df_list_raw = []
    df_ROI = []
    try:
        # loop over the selected cells
        for index,coord in enumerate(coords):
            fig,ax = plt.subplots(1,3,figsize=(15,5))
            c = [int(x) for x in list(coord)]
            center = c 
            size = size_of_bbox_zoom 

            zoomed_im = zoomed_image(logger,im, center, size) 
            # crop the image around the selected cell

            im_r = zoomed_im

            logger.info(f"The shape of the image analyzed centered at {c} is {im_r.shape}\n")

            mean_list_bleached = []
            mean_list_unbleached = []
            coords_ROI_list = []

            frames = []
            # Get the shape of your image
            height, width = im_r[0,...].shape

            counter = 1
            plt.waitforbuttonpress()

            print('Click on the center of the unbleached spot then on the bleached spot finally on the background of the crop')
            print('Press any key to end the selection')

            logger.info(f'The image was actualized every {frame_actualization} frames\n')

            ## add the circles to the image (in the first frame to be able to actualize them after every frame)
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
            interpolation_values = []
            vmin_r = np.min(im_r.flatten())
            vmax_r = np.quantile(im_r.flatten(),0.999)
            for i in range(0,im_r.shape[0]):
                if counter % frame_actualization == 0 or i in frame_pre_bleach:
                    coords_ROI = {}
                    interpolation_values.append(i)
                    counter += 1
                    # Display the image
                    ax[0].imshow(im_r[i,...], cmap='viridis',zorder=0,vmin=vmin_r,vmax=vmax_r)                
                    ax[0].set_title(f'Frame {i}')

                    # before the FRAP frame, display the frame after frap to be able to see where the unbleached spot is

                    if i <= FRAP_frame:
                        ax[1].imshow(im_r[FRAP_frame,...], cmap='viridis',zorder=0,vmin=vmin_r,vmax=vmax_r)
                        ax[1].set_title(f'Frame {FRAP_frame} with detections at frame {previous_frame}')
                    else:
                        ax[1].imshow(im_r[i,...], cmap='viridis',zorder=0,vmin=vmin_r,vmax=vmax_r)
                        ax[1].set_title(f'Frame {i} with detections at frame {previous_frame}')

                    if i > 0:
                        ax[2].imshow(im_r[previous_frame,...], cmap='viridis',zorder=0,vmin=vmin_r,vmax=vmax_r)
                        ax[2].set_title(f'Frame {previous_frame} with detections at frame {previous_frame}')
                    else:
                        ax[2].imshow(im_r[i,...], cmap='viridis',zorder=0,vmin=vmin_r,vmax=vmax_r)
                        ax[2].set_title(f'Frame {i}')
                    
                    previous_frame = i
                    radius = radius_unbleach_spot
                    radius_b = radius_bleach_spot
                    # Create a circle patch
                    try:
                        a = plt.ginput(2) # select the unbleached spot, the bleached spot and the background
                        x,y = a[0]
                        x_b,y_b = a[1]
                    except IndexError:
                        df = pd.DataFrame([mean_list_bleached,mean_list_unbleached],
                            index=['mean_list_bleached','mean_list_unbleached'])
                        df = df.T
                        df['nucleus'] = [index]*len(df)

                        # save coordinates of the ROI

                        df_ROI = pd.DataFrame(coords_ROI_list)

                        # save the data

                        df.rename(columns={'Unnamed: 0':'time'},inplace=True)
                        df.to_csv(save_path.split('/')[-1]+f'_raw_stopped_at_{i}_{token}.csv')

                        df_ROI.to_csv(save_path.split('/')[-1]+f'_ROI_stopped_at_{i}_{token}.csv')

                        logger.info(f"The analysis was stopped at frame {i}\n")
                    
                    coords_ROI['unbleached'] = [x,y]
                    coords_ROI['bleached'] = [x_b,y_b]
                    coords_ROI['frame'] = i
                    coords_ROI_list.append(coords_ROI)

                    # Create an array of indices
                    y_indices, x_indices = np.ogrid[:height, :width]
                    y_indices_b, x_indices_b = np.ogrid[:height, :width]

                    # Create a binary mask where the pixels inside the circle are True
                    mask_unbleached = (x_indices - x)**2 + (y_indices - y)**2 <= radius**2
                    mask_bleached = (x_indices_b - x_b)**2 + (y_indices_b - y_b)**2 <= radius_b**2

                    # Use the mask to index into your image and extract the pixel values
                    pixels_in_unbleached = im_r[i,...][mask_unbleached]
                    pixels_in_bleached = im_r[i,...][mask_bleached]

                    # Actualize the coordinate of the circles to be able to plot them in the next frame
                    c_plot.center = x, y
                    c_plot.radius = radius
                    c_plot_b.center = x_b, y_b
                    c_plot_b.radius = radius_b

                    c_plot_2.center = x, y
                    c_plot_2.radius = radius
                    c_plot_b_2.center = x_b, y_b
                    c_plot_b_2.radius = radius_b


                    # compute the mean intensity of the pixels inside the circles
                    mean_list_unbleached.append(np.mean(pixels_in_unbleached))
                    mean_list_bleached.append(np.mean(pixels_in_bleached))
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

            # put all the data in a dataframe

            df = pd.DataFrame([mean_list_bleached,mean_list_unbleached],
                            index=['mean_list_bleached','mean_list_unbleached'])
            df = df.T
            df['nucleus'] = [index]*len(df)

            df_list_raw.append(df)

            df = pd.DataFrame(coords_ROI_list)
            df['nucleus'] = [index]*len(df)

            df_ROI.append(df)

            # remove the circles between each analyzed cells

            c_plot.remove()
            c_plot_b.remove()
            c_plot_2.remove()
            c_plot_b_2.remove()
            c_plot_bck.remove()
            c_plot_bck_2.remove()
            fig.clear()

        df_list_raw = pd.concat(df_list_raw)
        df_list_raw.rename(columns={'Unnamed: 0':'time'},inplace=True)
        df_list_raw.to_csv(save_path.split('/')[-1]+f'_raw_{token}.csv',index=False)
        df_ROI = pd.concat(df_ROI)
        df_ROI.rename(columns={'Unnamed: 0':'time'},inplace=True)
        df_ROI.to_csv(save_path.split('/')[-1]+f'_ROI_{token}.csv',index=False)

        logger.info(f"The values were interpolated at {interpolation_values} \n")
        # logger.info(f"Created the output file {save_path.split('/')[-1]}.npy\n")

        logger.info("Done!")
    # save the data
    except Exception as e:
        logger.error(f"Error: {e}\n")
        df_list_raw = pd.concat(df_list_raw)
        df_list_raw.rename(columns={'Unnamed: 0':'time'},inplace=True)
        df_list_raw.to_csv(save_path.split('/')[-1]+f'_raw_{token}.csv',index=False)
        df_ROI = pd.concat(df_ROI)
        df_ROI.rename(columns={'Unnamed: 0':'time'},inplace=True)
        df_ROI.to_csv(save_path.split('/')[-1]+f'_ROI_{token}.csv',index=False)

        logger.info(f"The values were interpolated at {interpolation_values} \n")
        # logger.info(f"Created the output file {save_path.split('/')[-1]}.npy\n")

        logger.info("Done!")


# Execute the file
    
path = os.getcwd()

if __name__ == "__main__":

    from build_interactive_config import CONFIG_NAME

    with open(path+'/'+CONFIG_NAME, "r") as f:
        config = yaml.safe_load(f)

    # DEBUG
    # profiler = cProfile.Profile()
    # profiler.enable()
    main(**config)
    # profiler.disable()
    # profiler.print_stats(sort='time')
    # profiler.dump_stats("profiler_results.pstats")
    # END DEBUG
