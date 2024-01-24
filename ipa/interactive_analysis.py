import pandas as pd
import numpy as np
import tifffile as tiff
from tqdm import tqdm
from scipy import ndimage
from skimage.filters import threshold_otsu
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import interp1d
import yaml


def zoomed_image(im, center, size):
    # Calculate the top left and bottom right coordinates of the square
    top_left = (center[1] - size // 2, center[0] - size // 2)
    bottom_right = (center[1] + size // 2, center[0] + size // 2)

    # Slice the image array to create the zoomed image
    zoomed_im = im[:, top_left[0]:bottom_right[0], top_left[1]:bottom_right[1]]

    return zoomed_im


def compute_lab (im_roi):
    labels_final = np.zeros_like(im_roi)

    for frame in tqdm(range(im_roi.shape[0])):
        labels = ndimage.binary_fill_holes(im_roi[frame,...] > threshold_otsu(im_roi[frame,...]))
        labs, _ = ndimage.label(labels)
        #count pixels of each component and sort them by size, excluding the background
        vol_list = []
        label_unique = np.unique(labs)

        for labl in label_unique:
            if labl != 0:
                vol_list.append(np.count_nonzero(labs == labl))

        #create binary array of only the largest component
        # binary_mask = labs
        binary_mask = np.zeros(labs.shape)
        binary_mask = np.where(labs == vol_list.index(max(vol_list))+1, 1, 0)
        labels_final[frame,...] = binary_mask
    return labels_final


with open('test_yaml.yml', 'r') as file:
    params = yaml.safe_load(file)


im = tiff.imread(params['im_path'])

plt.waitforbuttonpress()
fig,ax = plt.subplots(1,2,figsize=(15,5))
ax[0].imshow(im[0,...],cmap='viridis')
ax[1].imshow(im[params['FRAP_frame'],...],cmap='viridis')
ax[0].set_title('pre-FRAP image')
ax[1].set_title('FRAP image')

if plt.waitforbuttonpress():
    plt.close()

plt.waitforbuttonpress()
number = 1# input('How many cells (ROIs) do you want to analyze?')

fig,ax = plt.subplots(1,2,figsize=(15,5))
ax[0].imshow(im[0,...],cmap='viridis')
ax[1].imshow(im[params['FRAP_frame'],...],cmap='viridis')
ax[0].set_title('pre-FRAP image')
ax[1].set_title('FRAP image')


coords = plt.ginput(int(number))

if plt.waitforbuttonpress():
    plt.close()


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
    size = params['size_of_bbox_zoom']  # Replace with the actual size


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

    for i in range(0,im_r.shape[0]):
        if counter % params['frame_actualization'] == 0 or i in params['frame_pre_bleach']:
            counter += 1

            # Display the image
            plt.subplot(1,2,1)
            plt.imshow(im_r[i,...], cmap='viridis')
            plt.title(f'Frame {i}')

            radius = params['radius_unbleach_spot']
            radius_b = params['radius_bleach_spot']
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


    # Original x values
    x_values = np.array(params['interpolation_values'])

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
    plt.plot(interpolated_values_unbleached[5:],marker='.',label='mean intensity unbleached')
    plt.plot(interpolated_values_bleached[5:],marker='.',label='mean intensity bleached')
    plt.scatter(frames[5:],mean_list_unbleached[5:],marker='o',label='points unbleached')
    plt.scatter(frames[5:],mean_list_bleached[5:],marker='o',label='points bleached')
    plt.plot(intensity_bleach[5:],marker='.',label='bleach of fluorophore')
    plt.plot(int_background[5:],marker='.',label='background')

    plt.legend()
    plt.subplot(1,2,2)
    plt.plot(frames_m[5:],iFRAP[5:],marker='.',label='iFRAP')
    plt.legend()
    plt.show()

np.save(params['save_path']+'/'+params['name_of_experiment']+'.npy',ifrap)