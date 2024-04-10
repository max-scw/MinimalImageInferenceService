import requests
import urllib.parse

from typing import Union, Dict, List
import logging


from DataModels import CameraInfo


def trigger_camera(camera_info: CameraInfo) -> Union[bytes, None]:
    """
    wrapper
    :param camera_info:
    :return:
    """
    url = build_url(camera_info)
    msg = f"trigger_camera(): url={url}"
    logging.debug(msg)
    print("DEBUG: " + msg)

    return request_camera(url)


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


def request_camera(address: str) -> Union[bytes, None]:
    msg = f"Requesting camera {address}"
    logging.debug(msg)
    print("DEBUG request_camera(): " + msg)
    r = requests.get(url=address)

    status_code = r.status_code
    # status codes
    # 1xx: Informational – Communicates transfer protocol-level information.
    # 2xx: Success – Indicates that the client’s request was accepted successfully.
    # 3xx: Redirection – Indicates that the client must take some additional action in order to complete their request.
    # 4xx: Client Error – This category of error status codes points the finger at clients.
    # 5xx: Server Error – The server takes responsibility for these error status codes.
    content = None
    if 200 <= status_code < 300:
        # output buffer
        content = r.content
    elif 400 <= status_code < 600:
        # error
        raise Exception(f"Server returned status code {status_code}")
    return content


def request_model_inference(
        address: str,
        image_raw: bytes,
        extension: str
) -> Dict[str, Union[List[int], List[float], List[List[float]]]]:
    msg = f"request_model_inference({address}, image={len(image_raw)}, extension={extension})"
    logging.debug(msg)
    print("DEBUG request_model_inference(): " + msg)

    # Send the POST request with the image
    ext = extension.strip(".")
    content = {"file": (f"image.{ext}", image_raw, f"image/{ext}")}

    response = requests.post(address, files=content)

    msg = f"request_model_inference(): {response}"
    logging.info(msg)
    print("INFO request_model_inference(): " + msg)

    # Check the response
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Inference returned status code {response.status_code} with message {response.text}")