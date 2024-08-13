from DataModels_BaslerCameraAdapter import PhotoParams, BaslerCameraSettings
from typing import Union, List, Tuple, Dict, Any


def get_basler_camera_parameter_from_config(config: Dict[str, Any]) -> BaslerCameraSettings:

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
        pixel_format=config["CAMERA_PIXEL_TYPE"] if "CAMERA_PIXEL_TYPE" in config else "Undefined",
        convert_to_format=config["CAMERA_CONVERT_TO_FORMAT"] if "CAMERA_CONVERT_TO_FORMAT" in config else "null",
    )

    return camera_info


def get_photo_parameter_from_config(config: Dict[str, Any]) -> PhotoParams:
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
        photo_params.exposure_time_microseconds = exposure_time_microseconds

    return photo_params
