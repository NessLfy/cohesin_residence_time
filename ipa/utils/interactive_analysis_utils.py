
import numpy as np
from tqdm import tqdm
from scipy import ndimage
from skimage.filters import threshold_otsu
from sklearn.metrics import confusion_matrix
import logging
from datetime import datetime

def zoomed_image(logger:logging.Logger,im:np.array, center:tuple, size:int) -> np.array:
    """
    This function takes in an image array and returns a zoomed image array.
    The zoomed image is a square of size 'size' centered at 'center'.
    If the zoomed image is out of bounds, the function returns the original image.

    Args:
        im (np.array): Image array
        center (tuple): Center of the zoomed image
        size (int): Size of the zoomed image

    Returns:
        np.array: Zoomed image array
    """

    # Calculate the top left and bottom right coordinates of the square
    top_left = (center[1] - size // 2, center[0] - size // 2)
    bottom_right = (center[1] + size // 2, center[0] + size // 2)

    # Slice the image array to create the zoomed image
    zoomed_im = im[:, top_left[0]:bottom_right[0], top_left[1]:bottom_right[1]]

    if zoomed_im.shape[1] == 0 or zoomed_im.shape[2] == 0:
        logger.warning("Zoomed image is out of bounds. Trying half the size..\n")
        logger.info(f"=The size of the zoomed image is {zoomed_im.shape}\n")
        try: 
            top_left = (center[1] - size // 4, center[0] - size // 4)
            bottom_right = (center[1] + size // 4, center[0] + size // 4)
            # Slice the image array to create the zoomed image
            zoomed_im = im[:, top_left[0]:bottom_right[0], top_left[1]:bottom_right[1]]
            if zoomed_im.shape[1] == 0 or  zoomed_im.shape[2] == 0:
                logger.info(f"=The size of the zoomed image is {zoomed_im.shape}\n")
                raise Exception("The zoomed image is still out of bounds. Returning original image.")
        except Exception:
            logger.warning("The zoomed image is still out of bounds. Returning original image.\n")
            logger.info(f"=The size of the zoomed image is {zoomed_im.shape}\n")
            zoomed_im = im

    return zoomed_im


def compute_lab (im_roi:np.array) -> np.array:
    """
    This function takes in an image array and returns a labelled image array.
    The labelled image is obtained by thresholding the image using Otsu's method.
    The labelled image is then eroded and filled to remove noise and avoid computing the intensity of neighboring cells.

    Args:
        im_roi (np.array): Image array

    Returns:
        np.array: Labelled image array
    """

    labels_final = np.zeros_like(im_roi)

    for frame in tqdm(range(im_roi.shape[0])):
        labels = ndimage.binary_fill_holes(im_roi[frame,...] > threshold_otsu(im_roi[frame,...]))
        labels = ndimage.binary_erosion(labels,iterations=2)
        labs, _ = ndimage.label(labels)
        labels_final[frame,...] = labs
        
    return labels_final


def overlap(im_lab:np.array,center:tuple) -> list:
    """
    This function takes in a labelled image array and the coordinate of the center of the cell to consider and returns a list of images containing only one label correspong to the tracked-cell.
    The list of labels is obtained by computing the overlap between the labelled image and its subsequent frames.
    The label with the highest overlap (IoU) is chosen as the label for the subsequent frame.

    Args:
        im_lab (np.array): Labelled image array
        center (tuple): Center of the tracked-cell
    
    Returns:
        list: List of labels
    """

    labs = []
    for frame in tqdm(range(im_lab.shape[0]-1)):
        if frame == 0:
            lab_1 = im_lab[frame,...]
            # Get the label number
            label_number = lab_1[int(center[1]), int(center[0])]
            lab_1 = np.where(lab_1 == label_number,1,0)

        else:
            lab_1 = np.where(im_lab[frame,...] == matched_label[1],1,0)
        
        unique_labels1 = np.unique(lab_1)
        unique_labels2 = np.unique(im_lab[frame+1,...][im_lab[frame+1,...]>0])
        label1 = lab_1
        label2 = im_lab[frame+1,...]

        unique_labels_combined = np.union1d(unique_labels1, unique_labels2)
        unique_labels_combined_dict = dict(
            zip(unique_labels_combined, np.arange(len(unique_labels_combined)))
        )
        overlap_matrix = confusion_matrix(
            label1.ravel(), label2.ravel(), labels=unique_labels_combined
        )

        ious = {}

        for i in unique_labels1:
            for j in unique_labels2:

                index_1 = unique_labels_combined_dict[i]
                index_2 = unique_labels_combined_dict[j]

                overlap = overlap_matrix[index_1, index_2]
                if overlap == 0:
                    continue
                b1_sum = np.sum(overlap_matrix[index_1, :])
                b2_sum = np.sum(overlap_matrix[:, index_2])
                union = b1_sum + b2_sum - overlap
                iou = overlap / union
                ious[(i, j)] = iou

        matched_label = list(ious.keys())[np.argmax(list(ious.values()))]

        labs.append(matched_label[1])
    return labs

def _create_logger(name: str) -> logging.Logger:
    """
    Create logger which logs to <timestamp>-<name>.log inside the current
    working directory.

    Args: 
        name (str): Name of the logger
    
    Returns:
        logging.Logger: Logger
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

