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
    if im_path == "": im_path = "/Volumes/tungsten/scratch/ggiorget/nessim/microscopy_data/FRAP_Rad21_halo/20231124_FRAP_WAPL_AID_NIPBL_FKBP/20231124_FRAP_NIPBL_FKBP_Rad21_Halo_561_1_conf561Triple-LP-FRAP.ome.tf2"
    
    size_of_bbox_zoom = questionary.path("Size of bbox zoom:").ask()
    if size_of_bbox_zoom == "": size_of_bbox_zoom = 100

    frame_actualization = questionary.path("Frame actualization:").ask()
    if frame_actualization == "": frame_actualization = 25

    frame_pre_bleach = questionary.path("Frame pre bleach:").ask()
    if frame_pre_bleach == "": frame_pre_bleach = [0,1,2,3,5,249]

    radius_unbleach_spot = questionary.path("Radius unbleach spot:").ask()
    if radius_unbleach_spot == "": radius_unbleach_spot = 5

    radius_bleach_spot = questionary.path("Radius bleach spot:").ask()
    if radius_bleach_spot == "": radius_bleach_spot = 7

    interpolation_values = questionary.path("Interpolation values:").ask()
    if interpolation_values == "": interpolation_values =  [0,1,2,3,5, 24, 49, 74, 99, 124, 149, 174, 199, 224, 249]

    save_path = questionary.path("Save path:").ask()
    if save_path == "": save_path = '/Users/louaness/Documents/cohesin_residence_time/cohesin_residence_time/runs/'
    
    save_path = os.path.join(save_path)

    config = {
        "name_of_experiment": name_of_experiment,
        "FRAP_frame": FRAP_frame,
        "im_path": im_path,
        "size_of_bbox_zoom": size_of_bbox_zoom,
        "frame_actualization": frame_actualization,
        "frame_pre_bleach": frame_pre_bleach,
        "radius_unbleach_spot": radius_unbleach_spot,
        "radius_bleach_spot": radius_bleach_spot,
        "interpolation_values": interpolation_values,
        "save_path": os.path.relpath(save_path,cwd)
    }

    os.makedirs(save_path+'/'+name_of_experiment, exist_ok=True)

    confi = os.path.join(save_path,name_of_experiment ,CONFIG_NAME)

    with open(os.path.join(save_path,name_of_experiment ,CONFIG_NAME), "w") as f:
        yaml.safe_dump(config, f)

    return confi

if __name__ == "__main__":
    config = main()