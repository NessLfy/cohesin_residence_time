
import numpy as np
from tqdm import tqdm
from scipy import ndimage
from skimage.filters import threshold_otsu

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