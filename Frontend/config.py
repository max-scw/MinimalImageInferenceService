from pathlib import Path
from datetime import datetime
import logging

from utils import get_config, get_env_variable
from utils_streamlit import ImpressInfo

from utils_config import get_image_parameter_from_config, get_basler_camera_parameter_from_config
from DataModels import SettingsMain
from DataModels_BaslerCameraAdapter import ImageParams, BaslerCameraSettings
from DataModelsFrontend import AppSettings

from typing import Union, List, Tuple


def look_for_file(filename: Union[str, Path], folders: List[Path]) -> Path:
    path = Path()
    for p2fl in [filename] + [Path(el) / filename for el in folders]:
        if Path(p2fl).is_file():
            path = Path(p2fl)
            break
    return path


def get_config_from_environment_variables() -> Tuple[BaslerCameraSettings, ImageParams, SettingsMain, AppSettings]:
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

    camera_info = get_basler_camera_parameter_from_config(config)
    image_params = get_image_parameter_from_config(config)

    # general settings
    settings_backend = SettingsMain()
    if "BACKEND_MIN_CONFIDENCE" in config:
        settings_backend.min_score = config["BACKEND_MIN_CONFIDENCE"]
    if "BACKEND_PATTERN_KEY" in config:
        settings_backend.pattern_key = config["BACKEND_PATTERN_KEY"]
    if "BACKEND_AUTH_TOKEN" in config:
        settings_backend.token = config["BACKEND_AUTH_TOKEN"]

    app_settings = AppSettings(
        address_backend=config["BACKEND_URL_BACKEND"],
        data_folder=config["GENERAL_DATA_FOLDER"],
        impress=impress,
        title=config["GENERAL_TITLE"] if "GENERAL_TITLE" in config else None,
        description=config["GENERAL_DESCRIPTION"] if "GENERAL_DESCRIPTION" in config else None,
        # file_type_save_image=config["GENERAL_FILE_TYPE_SAVE_IMAGE"],
        # bbox_pattern=load_yaml(config["GENERAL_FILE_BOX_PATTERN"]) if "GENERAL_FILE_BOX_PATTERN" in config else None,
        image_size=config["GENERAL_IMAGE_SIZE"] if "GENERAL_IMAGE_SIZE" in config else None,
    )

    return camera_info, image_params, settings_backend, app_settings


def get_page_title(default_prefix: str = "") -> Union[str, None]:
    prefix = get_env_variable("PREFIX", default_prefix)
    key = "IMPRESS_PROJECT_NAME"
    if prefix:
        key = f"{prefix}_{key}"
    return get_env_variable(key, None)
