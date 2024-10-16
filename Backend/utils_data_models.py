from DataModels import CameraInfo
from utils_config import get_basler_camera_parameter_from_config
from typing import Tuple, Dict, Any, Union


def get_camerainfo_parameter_from_config(config: Dict[str, Any]) -> CameraInfo:

    camera_info = CameraInfo(
        url=config["CAMERA_URL"],
        # camera
        **get_basler_camera_parameter_from_config(config).model_dump()
    )

    return camera_info

