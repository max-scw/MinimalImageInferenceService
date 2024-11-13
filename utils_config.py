from DataModels_BaslerCameraAdapter import (
    # PhotoParams,
    BaslerCameraSettings,
    # get_not_none_values,
    ImageParams
)
from typing import Union, List, Tuple, Dict, Any


def get_basler_camera_parameter_from_config(config: Dict[str, Any]) -> BaslerCameraSettings:

    camera_info = BaslerCameraSettings(
        # camera addresses
        serial_number=config["CAMERA_SERIAL_NUMBER"] if ("CAMERA_SERIAL_NUMBER" in config) and isinstance(config["CAMERA_SERIAL_NUMBER"], int) else None,
        ip_address=config["CAMERA_IP_ADDRESS"] if "CAMERA_IP_ADDRESS" in config else None,
        subnet_mask=config["CAMERA_SUBNET_MASK"] if "CAMERA_SUBNET_MASK" in config else None,
        # camera communication
        transmission_type=config["CAMERA_TRANSMISSION_TYPE"] if "CAMERA_TRANSMISSION_TYPE" in config else None,
        destination_ip_address=config["CAMERA_DESTINATION_IP_ADDRESS"]if "CAMERA_DESTINATION_IP_ADDRESS" in config else None,
        destination_port=config["CAMERA_DESTINATION_PORT"] if ("CAMERA_DESTINATION_PORT" in config) and isinstance(config["CAMERA_DESTINATION_PORT"], int) else None,
        # camera general
        pixel_format=config["CAMERA_PIXEL_TYPE"] if "CAMERA_PIXEL_TYPE" in config else "Undefined",
        convert_to_format=config["CAMERA_CONVERT_TO_FORMAT"] if "CAMERA_CONVERT_TO_FORMAT" in config else "null",
    )

    return camera_info


def get_image_parameter_from_config(config: Dict[str, Any]) -> ImageParams:
    return ImageParams(
        # image
        format=config["CAMERA_IMAGE_FORMAT"] if "CAMERA_IMAGE_FORMAT" in config else None,
        quality=config["CAMERA_IMAGE_QUALITY"] if "CAMERA_IMAGE_QUALITY" in config else None,
        # rotate
        rotation_angle=config["CAMERA_IMAGE_ROTATION_ANGLE"] if "CAMERA_IMAGE_ROTATION_ANGLE" in config else None,
        rotation_expand=config["CAMERA_IMAGE_ROTATION_EXPAND"] if "CAMERA_IMAGE_ROTATION_EXPAND" in config else None,
        # crop
        roi_left=config["CAMERA_IMAGE_ROI_LEFT"] if "CAMERA_IMAGE_ROI_LEFT" in config else None,
        roi_top=config["CAMERA_IMAGE_ROI_TOP"] if "CAMERA_IMAGE_ROI_TOP" in config else None,
        roi_right=config["CAMERA_IMAGE_ROI_RIGHT"] if "CAMERA_IMAGE_ROI_RIGHT" in config else None,
        roi_bottom=config["CAMERA_IMAGE_ROI_BOTTOM"] if "CAMERA_IMAGE_ROI_BOTTOM" in config else None,
        )

