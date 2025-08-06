"""
build_preprocessing_config.py
=============================

Ask for user input via command line interface (CLI) to build the
preprocessing_config.yaml. The preprocessing_config.yaml is consumed
by the run_preprocessing.py script.
"""


import os
import questionary
import yaml



CONFIG_NAME = 'config_file.yml'


def main() -> None:
    """
    Create preprocessing_config.yaml from user inputs.
    """
    cwd = os.getcwd()

    print("Please answer the following questions to build the config file. \n Press enter to use the default values.")

    name_of_experiment = questionary.path("Name of experiment:").ask()
    if name_of_experiment == "": name_of_experiment = "test"

    FRAP_frame = questionary.path("FRAP frame:").ask()
    if FRAP_frame == "": FRAP_frame = 4

    im_path = questionary.path("Path to image:").ask()
    if im_path == "": raise ValueError("Path to image cannot be empty. Please provide a valid path.")
    
    size_of_bbox_zoom = questionary.path("Size of bbox zoom:").ask()
    if size_of_bbox_zoom == "": size_of_bbox_zoom = 100
    else: size_of_bbox_zoom = int(size_of_bbox_zoom)

    frame_actualization = questionary.path("Frame actualization:").ask()
    if frame_actualization == "": frame_actualization = 25
    else : frame_actualization = int(frame_actualization)

    frame_pre_bleach = questionary.path("Frame pre bleach:").ask()
    if frame_pre_bleach == "": frame_pre_bleach = [0,1,2,3,4,249]

    radius_unbleach_spot = questionary.path("Radius unbleach spot:").ask()
    if radius_unbleach_spot == "": radius_unbleach_spot = 5
    else: radius_unbleach_spot = int(radius_unbleach_spot)

    radius_bleach_spot = questionary.path("Radius bleach spot:").ask()
    if radius_bleach_spot == "": radius_bleach_spot = 7
    else: radius_bleach_spot = int(radius_bleach_spot)

    save_path = questionary.path("Save path:").ask()
    if save_path == "": raise ValueError("Save path cannot be empty. Please provide a valid path.")
    
    confi = os.path.join(save_path,name_of_experiment ,CONFIG_NAME)

    config = {
        "name_of_experiment": name_of_experiment,
        "FRAP_frame": FRAP_frame,
        "im_path": im_path,
        "size_of_bbox_zoom": size_of_bbox_zoom,
        "frame_actualization": frame_actualization,
        "frame_pre_bleach": frame_pre_bleach,
        "radius_unbleach_spot": radius_unbleach_spot,
        "radius_bleach_spot": radius_bleach_spot,
        "save_path": os.path.join(save_path,name_of_experiment)
    }

    os.makedirs(save_path+'/'+name_of_experiment, exist_ok=True)

    with open(os.path.join(save_path,name_of_experiment ,CONFIG_NAME), "w") as f:
        yaml.safe_dump(config, f)

    return confi

if __name__ == "__main__":
    config = main()