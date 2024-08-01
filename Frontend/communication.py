import requests
import urllib
from timeit import default_timer


from typing import Union, Dict, List, Any
import logging


from DataModels import OptionsReturnValuesMain, SettingsMain
from DataModels_BaslerCameraAdapter import BaslerCameraSettings, PhotoParams


def build_url(
        address: str,
        camera_params: BaslerCameraSettings,
        photo_params: PhotoParams,
        settings: SettingsMain,
):
    # address
    if not address.startswith(("http://", "https://")):
        address = "http://" + address

    # return options
    return_options = OptionsReturnValuesMain(
        decision=True,
        pattern_name=True,
        img=True,
        img_drawn=True,
        # details
        bboxes=True,
        class_ids=True,
        scores=True,
    )
    # join dictionaries
    parameter = camera_params.dict() | photo_params.dict() | settings.dict() | return_options.dict()

    # parameter
    params = {ky: vl for ky, vl in parameter.items() if (vl is not None) and (vl != "")}

    info = {ky: (vl, type(vl)) for ky, vl in params.items()}
    logging.debug(f"building URL for backend: {info}")
    # build url
    return f"{address}?{urllib.parse.urlencode(params)}"


def request_backend(
        address: str,
        camera_params: BaslerCameraSettings,
        photo_params: PhotoParams,
        settings: SettingsMain,
        timeout: int = 1000
) -> Union[Dict[str, Any], None]:

    url = build_url(address, camera_params, photo_params, settings)  # TODO: can be cached
    logging.debug(f"Request backend: {url}")

    t0 = default_timer()
    response = requests.get(url=url, timeout=timeout)
    status_code = response.status_code

    logging.info(
        f"Requesting camera {address} took {(default_timer() - t0) / 1000:.2} ms. "
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
        content = response.json()
    elif 400 <= status_code < 600:
        # error
        raise Exception(f"Server returned status code {status_code} with message {response.text}")
    return content

