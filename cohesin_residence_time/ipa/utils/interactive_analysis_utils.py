
import numpy as np
from tqdm import tqdm
from scipy import ndimage
from skimage.filters import threshold_otsu
from sklearn.metrics import confusion_matrix

def zoomed_image(logger,im, center, size):
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


def compute_lab (im_roi):
    labels_final = np.zeros_like(im_roi)

    for frame in tqdm(range(im_roi.shape[0])):
        labels = ndimage.binary_fill_holes(im_roi[frame,...] > threshold_otsu(im_roi[frame,...]))
        labels = ndimage.binary_erosion(labels,iterations=2)
        labs, _ = ndimage.label(labels)
        labels_final[frame,...] = labs
        
    return labels_final


def overlap(im_lab,center):
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
        #match_lab = np.where(im_lab[frame+1,...] == matched_label[1],1,0)
    return labs