from pathlib import Path
import tomllib
import yaml
from datetime import datetime
from ast import literal_eval
import os

from utils import get_environment_variables, get_env_variable
from utils_streamlit import ImpressInfo
from data_models import (ModelInfo, CameraInfo)
from app import main

from typing import Union, List


def look_for_file(filename: Union[str, Path], folders: List[Path]) -> Path:
    path = Path()
    for p2fl in [filename] + [Path(el) / filename for el in folders]:
        if p2fl.is_file():
            path = p2fl
            break
    return path


if __name__ == "__main__":
    # --- ONLY FOR DEBUGGING
    # env = {
    #     "TI_IMPRESS_PROJECT_NAME": "Test",
    #     "TI_IMPRESS_AUTHOR": "Timo Teststudent",
    #     "TI_IMPRESS_STATUS": "active, alpha test",
    #     "TI_IMPRESS_ADDITIONAL_INFO": None,
    #     "TI_IMPRESS_PROJECT_LINK": None
    #
    # }
    # for ky, vl in env.items():
    #     os.environ.setdefault(ky, vl)
    # ---

    # get config
    prefix = get_env_variable("PREFIX", "TI")

    # --- load default config
    with open(Path("./default_config.toml"), "rb") as fid:
        config_default = tomllib.load(fid)

    config_default_env = dict()
    for group in config_default:
        for ky, vl in config_default[group].items():
            # variable name
            var_nm = "_".join([group, ky]).upper()
            nm = "_".join([prefix, var_nm]).upper()
            config_default_env[var_nm] = vl if vl else None

    config = get_environment_variables(rf"{prefix}_", False) | config_default_env

    # impress
    impress = ImpressInfo(
        project_name=config["IMPRESS_PROJECT_NAME"],
        author=config["IMPRESS_AUTHOR"],
        status=config["IMPRESS_STATUS"],
        date_up_since=datetime.now(),
        additional_info=config["IMPRESS_ADDITIONAL_INFO"],
        project_link=config["IMPRESS_PROJECT_LINK"]
    )

    camera_info = CameraInfo(
        url=config["CAMERA_URL"],
        # exposure_time_microseconds: Optional[int] = 10000
        # camera addresses
        serial_number=config["CAMERA_SERIAL_NUMBER"],
        ip_address=config["CAMERA_IP_ADDRESS"],
        # config
        timeout_ms=config["CAMERA_TIMEOUT"],
        transmission_type=config["CAMERA_TRANSMISSION_TYPE"],
        destination_ip_address=config["CAMERA_DESTINATION_IP_ADDRESS"],
        destination_port=config["CAMERA_DESTINATION_PORT"],
        # debugging
        emulate_camera=config["CAMERA_EMULATE_CAMERA"] if config["CAMERA_EMULATE_CAMERA"] else False
    )

    filename = Path(config["MODEL_FILENAME"])
    folder_head = Path(config["MODEL_FOLDER_HEAD"])
    folder_data = Path(config["MODEL_FOLDER_DATA"])

    path_to_model = look_for_file(filename, [folder_head, folder_data])

    maps = dict()
    for ky in ["MODEL_CLASS_MAP", "MODEL_COLOR_MAP"]:
        mapping = config[ky]

        if mapping is None:
            map_ = None
        elif Path(mapping).suffix in (".yaml", ".yml"):
            # if is YAML file
            # identify path to file
            path_to_map = look_for_file(mapping, [folder_head, folder_data])
            # read file
            with open(path_to_map, "r") as fid:
                map_ = yaml.safe_load(fid)
        else:
            # else is string
            map_ = literal_eval(mapping)
            if isinstance(map_, list):
                # construct dictionary
                map_ = {i: el for i, el in enumerate(map_)}
        maps[ky] = map_

    model_info = ModelInfo(
        path=path_to_model,
        class_map=maps["MODEL_CLASS_MAP"],
        color_map=maps["MODEL_COLOR_MAP"],
        image_size=config["MODEL_IMAGE_SIZE"],
        precision=config["MODEL_PRECISION"]
    )

    main(
        model_info=model_info,
        camera_info=camera_info,
        # impress=impress
    )
