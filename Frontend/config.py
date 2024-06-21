from pathlib import Path
from datetime import datetime
import logging

from utils import get_config, get_env_variable
from utils_streamlit import ImpressInfo
# from utils_coordinates import load_yaml

from DataModels import CameraPhotoParameter, SettingsMain
from DataModelsFrontend import AppSettings

from typing import Union, List, Tuple


def look_for_file(filename: Union[str, Path], folders: List[Path]) -> Path:
    path = Path()
    for p2fl in [filename] + [Path(el) / filename for el in folders]:
        if Path(p2fl).is_file():
            path = Path(p2fl)
            break
    return path


def get_config_from_environment_variables() -> Tuple[CameraPhotoParameter, SettingsMain, AppSettings]:
    config = get_config(default_prefix="TI")
    logging.info(f"App configuration: {config}")

    # impress
    impress = ImpressInfo(
        project_name=config["IMPRESS_PROJECT_NAME"],
        author=config["IMPRESS_AUTHOR"],
        status=config["IMPRESS_STATUS"],
        date_up_since=datetime.now(),
        additional_info=config["IMPRESS_ADDITIONAL_INFO"],
        project_link=config["IMPRESS_PROJECT_LINK"]
    )

    camera_info = CameraPhotoParameter(
        # exposure_time_microseconds: Optional[int] = 10000
        # camera addresses
        serial_number=config["CAMERA_SERIAL_NUMBER"],
        ip_address=config["CAMERA_IP_ADDRESS"],
        subnet_mask=config["CAMERA_SUBNET_MASK"],
        # config
        timeout=config["CAMERA_TIMEOUT"],
        transmission_type=config["CAMERA_TRANSMISSION_TYPE"],
        destination_ip_address=config["CAMERA_DESTINATION_IP_ADDRESS"],
        destination_port=config["CAMERA_DESTINATION_PORT"],
        # image
        format=config["CAMERA_IMAGE_FORMAT"],
        quality=config["CAMERA_IMAGE_QUALITY"],
        # debugging
        emulate_camera=config["CAMERA_EMULATE_CAMERA"] if config["CAMERA_EMULATE_CAMERA"] else False
    )

    settings_backend = SettingsMain()
    if "GENERAL_MIN_CONFIDENCE" in config:
        settings_backend.min_score = config["GENERAL_MIN_CONFIDENCE"]
    if "GENERAL_PATTERN_KEY" in config:
        settings_backend.pattern_key = config["GENERAL_PATTERN_KEY"]

    # folder_head = Path(config["MODEL_FOLDER_HEAD"])
    # folder_data = Path(config["MODEL_FOLDER_DATA"])
    #
    # maps = dict()
    # for ky in ["MODEL_CLASS_MAP", "MODEL_COLOR_MAP"]:
    #     mapping = config[ky]
    #
    #     if mapping is None or mapping == "":
    #         map_ = None
    #     elif Path(mapping).suffix in (".yaml", ".yml"):
    #         # if is YAML file:
    #         # identify path to file
    #         path_to_map = look_for_file(mapping, [folder_head, folder_data])
    #         logging.info(f"configuration: {ky}. YAML file {path_to_map}.")
    #         # read file
    #         if path_to_map.is_file():
    #             with open(path_to_map, "r") as fid:
    #                 map_ = yaml.safe_load(fid)
    #         else:
    #             map_ = None
    #     elif Path(mapping).suffix in (".txt", ".conf"):
    #         # if is text file:
    #         # identify path to file
    #         path_to_map = look_for_file(mapping, [folder_head, folder_data])
    #         logging.info(f"configuration: {ky}. Text file {path_to_map}.")
    #         # read file
    #         if path_to_map.is_file():
    #             with open(path_to_map, "r") as fid:
    #                 lines = fid.readlines()
    #             map_ = {i: ln.strip() for i, ln in enumerate(lines) if len(ln) > 3}
    #         else:
    #             map_ = None
    #     else:
    #         # else is string
    #         map_ = literal_eval(mapping)
    #         if isinstance(map_, list):
    #             # construct dictionary
    #             map_ = {i: el for i, el in enumerate(map_)}
    #     maps[ky] = map_
    #
    # model_info = ModelInfo(
    #     # url=config["MODEL_URL"],
    #     class_map=maps["MODEL_CLASS_MAP"],
    #     color_map=maps["MODEL_COLOR_MAP"],
    # )

    app_settings = AppSettings(
        address_backend=config["GENERAL_URL_BACKEND"],
        data_folder=config["GENERAL_DATA_FOLDER"],
        impress=impress,
        title=config["GENERAL_TITLE"] if "GENERAL_TITLE" in config else None,
        description=config["GENERAL_DESCRIPTION"] if "GENERAL_DESCRIPTION" in config else None,
        # file_type_save_image=config["GENERAL_FILE_TYPE_SAVE_IMAGE"],
        # bbox_pattern=load_yaml(config["GENERAL_FILE_BOX_PATTERN"]) if "GENERAL_FILE_BOX_PATTERN" in config else None,
        image_size=config["GENERAL_IMAGE_SIZE"] if "GENERAL_IMAGE_SIZE" in config else None,
    )

    return camera_info, settings_backend, app_settings


def get_page_title(default_prefix: str = "") -> Union[str, None]:
    prefix = get_env_variable("PREFIX", default_prefix)
    key = "IMPRESS_PROJECT_NAME"
    if prefix:
        key = f"{prefix}_{key}"
    return get_env_variable(key, None)

