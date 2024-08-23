import requests
import urllib.parse
from timeit import default_timer

from DataModels import CameraInfo, ResultInference
from DataModels_BaslerCameraAdapter import (
    PhotoParams,
    BaslerCameraSettings,
    get_not_none_values
)
from utils import setup_logging

from typing import Union, Dict, List


# Setup logging
logger = setup_logging(__name__)


def trigger_camera(
        camera_info: CameraInfo,
        photo_params: PhotoParams,
        timeout: int = 5  # seconds
) -> Union[bytes, None]:
    """
    wrapper
    """
    # synchronize timeout between request and pylon.RetrieveImage function
    camera_info.timeout_ms = int(timeout * 1000)

    t0 = default_timer()
    url = build_url(camera_info, photo_params)
    t1 = default_timer()
    logger.debug(f"trigger_camera(): url={url} (building url took {(t1 - t0) * 1000:.4g} ms)")

    response = request_camera(url, timeout)
    t2 = default_timer()
    logger.debug(f"trigger_camera(): request_camera(url, timeout={timeout}) (took {(t2 - t1) * 1000:.4g} ms)")
    return response


def build_url(camera_info: CameraInfo, photo_params: PhotoParams) -> str:
    params = {
        ky: vl for ky, vl in get_not_none_values(camera_info).items()
        if ky in BaslerCameraSettings.model_fields
    }
    # merge with photo parameter
    params |= get_not_none_values(photo_params)
    # build url
    url = camera_info.url + f"?{urllib.parse.urlencode(params)}"
    return url


def request_camera(
        address: str,
        timeout: int = 5  # seconds
) -> Union[bytes, None]:

    t0 = default_timer()
    response = requests.get(url=address, timeout=timeout)
    status_code = response.status_code
    t1 = default_timer()
    logger.info(
        f"Requesting camera {address} took {(t1 - t0) * 1000:.4g} ms. "
        f"(Status code: {status_code})"
    )

    # status codes
    # 1xx: Informational – Communicates transfer protocol-level information.
    # 2xx: Success – Indicates that the client’s request was accepted successfully.
    # 3xx: Redirection – Indicates that the client must take some additional action in order to complete their request.
    # 4xx: Client Error – This category of error status codes points the finger at clients.
    # 5xx: Server Error – The server takes responsibility for these error status codes.
    content = None
    if 200 <= status_code < 300:
        # output buffer
        content = response.content
    elif 400 <= status_code < 600:
        # error
        raise Exception(f"Server returned status code {status_code} with message {response.text}")

    return content


def request_model_inference(
        address: str,
        image_raw: bytes,
        extension: str,
        timeout: int = 5  # seconds
) -> ResultInference:

    logger.debug(f"request_model_inference({address}, image={len(image_raw)}, extension={extension})")

    # Send the POST request with the image
    ext = extension.strip(".")
    content = {"image": (f"image.{ext}", image_raw, f"image/{ext}")}

    t0 = default_timer()
    response = requests.post(address, files=content, timeout=timeout)
    status_code = response.status_code

    logger.info(
        f"Requesting model inference {address} took {(default_timer() - t0) / 1000:.2} ms. "
        f"(Status code: {status_code})"
    )

    logger.debug(f"request_model_inference(): {response}")

    # Check the response
    if status_code == 200:
        return response.json()
    else:
        raise Exception(f"Inference returned status code {status_code} with message {response.text}")
