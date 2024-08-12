import logging

from DataModels import CameraInfo, InferenceInfo

from typing import Tuple, Dict, Any, Union


def build_camera_info(config: Dict[str, Any]) -> CameraInfo:

    camera_info = CameraInfo(
        url=config["CAMERA_URL"],
        # exposure_time_microseconds: Optional[int] = 10000
        # camera addresses
        serial_number=config["CAMERA_SERIAL_NUMBER"] if "CAMERA_SERIAL_NUMBER" in config else None,
        ip_address=config["CAMERA_IP_ADDRESS"] if "CAMERA_IP_ADDRESS" in config else None,
        subnet_mask=config["CAMERA_SUBNET_MASK"] if "CAMERA_SUBNET_MASK" in config else None,
        # config
        timeout_ms=config["CAMERA_TIMEOUT"] if "CAMERA_TIMEOUT" in config else None,
        transmission_type=config["CAMERA_TRANSMISSION_TYPE"] if "CAMERA_TRANSMISSION_TYPE" in config else None,
        destination_ip_address=config["CAMERA_DESTINATION_IP_ADDRESS"] if "CAMERA_DESTINATION_IP_ADDRESS" in config else None,
        destination_port=config["CAMERA_DESTINATION_PORT"] if "CAMERA_DESTINATION_PORT" in config else None,
        image_extension=config["CAMERA_IMAGE_EXTENSION"] if "CAMERA_IMAGE_EXTENSION" in config else None,
        # debugging
        emulate_camera=config["CAMERA_EMULATE_CAMERA"] if config["CAMERA_EMULATE_CAMERA"] else False
    )

    # set exposure time if environment variable exists and has a valid format
    exposure_time_microseconds = None
    for ky in ["CAMERA_EXPOSURE_TIME", "CAMERA_EXPOSURE_TIME_MICROSECONDS"]:
        if (ky in config) and isinstance(config[ky], int):
            exposure_time_microseconds = config[ky]
    if exposure_time_microseconds:
        camera_info.exposure_time = exposure_time_microseconds

    return camera_info
