from pathlib import Path
from datetime import datetime
import logging

from utils import get_config, get_env_variable
from utils_streamlit import ImpressInfo
# from utils_coordinates import load_yaml

from DataModels import SettingsMain
from DataModels_BaslerCameraAdapter import PhotoParams, BaslerCameraSettings
from DataModelsFrontend import AppSettings

from typing import Union, List, Tuple


def look_for_file(filename: Union[str, Path], folders: List[Path]) -> Path:
    path = Path()
    for p2fl in [filename] + [Path(el) / filename for el in folders]:
        if Path(p2fl).is_file():
            path = Path(p2fl)
            break
    return path


def get_config_from_environment_variables() -> Tuple[BaslerCameraSettings, PhotoParams, SettingsMain, AppSettings]:
    config = get_config()
    logging.info(f"App configuration: {config}")

    # impress
    impress = ImpressInfo(
        project_name=config["IMPRESS_PROJECT_NAME"],
        author=config["IMPRESS_AUTHOR"],
        status=config["IMPRESS_STATUS"],
        date_up_since=datetime.now(),
        additional_info=config["IMPRESS_ADDITIONAL_INFO"] if "IMPRESS_ADDITIONAL_INFO" in config else None,
        project_link=config["IMPRESS_PROJECT_LINK"]
    )

    camera_info = BaslerCameraSettings(
        # camera addresses
        serial_number=config["CAMERA_SERIAL_NUMBER"] if isinstance(config["CAMERA_SERIAL_NUMBER"], int) else None,
        ip_address=config["CAMERA_IP_ADDRESS"],
        subnet_mask=config["CAMERA_SUBNET_MASK"],
        # camera communication
        transmission_type=config["CAMERA_TRANSMISSION_TYPE"],
        destination_ip_address=config["CAMERA_DESTINATION_IP_ADDRESS"],
        destination_port=config["CAMERA_DESTINATION_PORT"] if isinstance(config["CAMERA_DESTINATION_PORT"], int) else None,
        # camera general
        pixel_type=config["CAMERA_PIXEL_TYPE"] if "CAMERA_PIXEL_TYPE" in config else "Undefined",
        convert_to_format=config["CAMERA_CONVERT_TO_FORMAT"] if "CAMERA_CONVERT_TO_FORMAT" in config else "null",
    )

    photo_params = PhotoParams(
        # exposure_time_microseconds: Optional[int] = 10000
        # communication
        timeout=config["CAMERA_TIMEOUT"] if isinstance(config["CAMERA_TIMEOUT"], int) else None,
        # image
        format=config["CAMERA_IMAGE_FORMAT"],
        quality=config["CAMERA_IMAGE_QUALITY"],
        # debugging
        emulate_camera=config["CAMERA_EMULATE_CAMERA"] if config["CAMERA_EMULATE_CAMERA"] else False
    )
    # set exposure time if environment variable exists and has a valid format
    exposure_time_microseconds = None
    for ky in ["CAMERA_EXPOSURE_TIME", "CAMERA_EXPOSURE_TIME_MICROSECONDS"]:
        if (ky in config) and isinstance(config[ky], int):
            exposure_time_microseconds = config[ky]
    if exposure_time_microseconds:
        photo_params.exposure_time = exposure_time_microseconds

    # general settings
    settings_backend = SettingsMain()
    if "GENERAL_MIN_CONFIDENCE" in config:
        settings_backend.min_score = config["GENERAL_MIN_CONFIDENCE"]
    if "GENERAL_PATTERN_KEY" in config:
        settings_backend.pattern_key = config["GENERAL_PATTERN_KEY"]

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

    return camera_info, photo_params, settings_backend, app_settings


def get_page_title(default_prefix: str = "") -> Union[str, None]:
    prefix = get_env_variable("PREFIX", default_prefix)
    key = "IMPRESS_PROJECT_NAME"
    if prefix:
        key = f"{prefix}_{key}"
    return get_env_variable(key, None)

