import requests
import cv2 as cv
import numpy as np
import urllib.parse

from typing import Union


from data_models import CameraInfo


def trigger_camera(camera_info: CameraInfo) -> np.ndarray:
    """
    wrapper
    :param camera_info:
    :return:
    """
    return request_camera(build_url(camera_info))


def build_url(camera_info: CameraInfo) -> str:

    params = dict()
    if camera_info.exposure_time_microseconds is not None:
        params["exposure_time_microseconds"] = camera_info.exposure_time_microseconds

    if camera_info.serial_number is not None:
        params["serial_number"] = camera_info.serial_number
    elif camera_info.ip_address is not None:
        params["ip_address"] = camera_info.ip_address
    else:
        params["emulate_camera"] = True

    if camera_info.timeout_ms is not None:
        params["timeout"] = camera_info.timeout_ms

    if camera_info.transmission_type is not None:
        params["transmission_type"] = camera_info.transmission_type

    if camera_info.destination_ip_address is not None:
        params["destination_ip_address"] = camera_info.destination_ip_address
    if camera_info.transmission_type is not None:
        params["destination_port"] = camera_info.destination_port

    if camera_info.emulate_camera:
        params["emulate_camera"] = camera_info.emulate_camera

    # build url
    url = camera_info.url + f"?{urllib.parse.urlencode(params)}"
    return url


def request_camera(address: str) -> Union[np.ndarray, None]:
    print(f"Requesting camera {address}")
    r = requests.get(url=address)

    status_code = r.status_code
    # status codes
    # 1xx: Informational – Communicates transfer protocol-level information.
    # 2xx: Success – Indicates that the client’s request was accepted successfully.
    # 3xx: Redirection – Indicates that the client must take some additional action in order to complete their request.
    # 4xx: Client Error – This category of error status codes points the finger at clients.
    # 5xx: Server Error – The server takes responsibility for these error status codes.
    out = None
    if 200 <= status_code < 300:
        # success
        img_ary = np.frombuffer(r.content, np.uint8)
        out = cv.imdecode(img_ary, cv.IMREAD_COLOR)
    elif 400 <= status_code < 600:
        # error
        raise Exception(f"Server returned status code {status_code}")
    return out


