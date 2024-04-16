from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

from starlette.background import BackgroundTask
from pathlib import Path
from random import shuffle

from pypylon import pylon
import logging

from typing import List

# from Camera import BaslerPylonCameraWrapper
from Camera import BaslerPylonCameraWrapper2 as BaslerPylonCameraWrapper

from utils import get_env_variable



ENTRYPOINT_TEST = "/test"
ENTRYPOINT_TEST_BASLER = ENTRYPOINT_TEST + "/basler"
ENTRYPOINT_TEST_IMAGE = ENTRYPOINT_TEST + "/image"

ENTRYPOINT_BASLER = "/basler"
ENTRYPOINT_TAKE_PHOTO = ENTRYPOINT_BASLER + "/take-photo"
ENTRYPOINT_CAMERA_NAME = ENTRYPOINT_BASLER + "/get-camera-name"
ENTRYPOINT_CAMERA_INFO = ENTRYPOINT_BASLER + "/get-camera-info"


PATH_TO_TEMPORARY_FILES = Path("tmp")
MAX_NUM_TEMP_FILES = get_env_variable("MAX_NUM_TEMP_FILES", 10)

if not PATH_TO_TEMPORARY_FILES.exists():
    print(f"Creating folder {PATH_TO_TEMPORARY_FILES.as_posix()}.")
    PATH_TO_TEMPORARY_FILES.mkdir()

app = FastAPI()
app.mount("/temporary", StaticFiles(directory=PATH_TO_TEMPORARY_FILES), name="static")
PATH_TO_TEMPORARY_FILES.mkdir(exist_ok=True)
# create endpoint for prometheus
Instrumentator().instrument(app).expose(app)  # produces a False in the console every time a valid entrypoint is called


# ----- home
@app.get("/")
async def home():
    return {
        'Message': 'This is a minimal website & webservice to interact with a Basler camera.',
        'Entrypoints':
            [
                {
                    'Address': f'{ENTRYPOINT_CAMERA_NAME}',
                    'Description': 'returns the full name of the camera',
                    'Variables (one required)': ['serial_number',
                                                  'ip_address']
                },
                {
                    'Address': f'{ENTRYPOINT_CAMERA_INFO}',
                    'Description': 'returns the name (type), IP address and MAC address of the camera as JSON',
                    'Variables (one required)': ['serial_number',
                                                'ip_address']
                },
                {
                    'Address': f'{ENTRYPOINT_TAKE_PHOTO}',
                    'Description': 'Connects to a Basler camera via the CameraVision library pypylon and returns a '
                                    'photo.',
                    'Variables (one required)': ['serial_number',
                                                  'ip_address'],
                    'Variables (optional)': ['exposure_time_microseconds',
                                              'timeout',
                                              'transmission_type',
                                              'destination_ip_address',
                                              'destination_port']
                },
                # ---- TEST FUNCTIONS
                {
                    'Address': f'{ENTRYPOINT_TEST}',
                    'Description': 'negates the input variable. To test a functioning server',
                    'Variables (required)': ['boolean']
                },
                {
                    'Address': f'{ENTRYPOINT_TEST_BASLER}',
                    'Description': 'returns the status of two flags for connecting to the camera.',
                    'Variables (required)': ['serial_number']
                },
                {
                    'Address': f'{ENTRYPOINT_TEST_IMAGE}',
                    'Description': 'returns a test image.'
                }
            ],
            'Software': 'fastAPI',
            'Author': 'SCHWMAX'
            }


# ----- Interact with the Basler camera
# create global camera instance
CAMERA = BaslerPylonCameraWrapper(verbose=True)


@app.get(ENTRYPOINT_TAKE_PHOTO)
def take_photo(
        exposure_time_microseconds: int = None,
        serial_number: int = None,
        ip_address: str = None,
        emulate_camera: bool = False,
        timeout: int = None,
        transmission_type: str = None,
        destination_ip_address: str = None,
        destination_port: int = None
):
    port_max = 65535
    if destination_port and 1 < destination_port > port_max:
        raise ValueError(f"Destination port must be smaller than {port_max} but was destination_port={destination_port}")
    kwargs = {
        "serial_number": serial_number,
        "ip_address": ip_address,
        "emulate_camera": emulate_camera,
        "timeout": timeout,
        "transmission_type": transmission_type,
        "destination_ip_address": destination_ip_address,
        "destination_port": destination_port
    }
    elements = {ky: val for ky, val in kwargs.items() if val}
    logging.debug(f"take_photo({elements})")
    # try:
    CAMERA.set_settings(**kwargs)
    image_path = CAMERA.save_image(
        Path(PATH_TO_TEMPORARY_FILES),
        file_extension=".webp",
        exposure_time_microseconds=exposure_time_microseconds
    )
    # except ValueError as ve:
    #     raise HTTPException(status_code=449, detail=ve.args)

    logging.debug(f"Photo temporary saved to {image_path.as_posix()}.")

    return FileResponse(
        image_path.as_posix(),
        media_type='image/webp',
        background=BackgroundTask(limit_temp_files)
    )


@app.get(ENTRYPOINT_CAMERA_NAME)
def get_camera_name(
        serial_number: int = None,
        ip_address: str = None
):
    global CAMERA
    CAMERA.set_settings(serial_number=serial_number, ip_address=ip_address)
    if CAMERA.camera:
        return CAMERA.get_device_name()
    else:
        return "No camera created yet."


@app.get(ENTRYPOINT_CAMERA_INFO)
def get_camera_info(
        serial_number: int = None,
        ip_address: str = None
):
    global CAMERA
    CAMERA.set_settings(serial_number=serial_number, ip_address=ip_address)
    if CAMERA.camera:
        return CAMERA.get_device_info()
    else:
        return "No camera created yet."


# ----- helper functions
@app.on_event('shutdown')
def delete_all_temp_files():
    logging.info('shutting down ...')
    files = get_list_temp_files()
    for i, fl in enumerate(files):
        cleanup(fl.as_posix())


@app.on_event('startup')
def create_camera():
    logging.info('create new BaslerPylonCameraWrapper-object ...')
    global CAMERA
    CAMERA = BaslerPylonCameraWrapper(verbose=True)


def cleanup(temp_file: str):
    Path(temp_file).unlink()


def get_list_temp_files() -> List[Path]:
    # list all files
    files = list(Path(PATH_TO_TEMPORARY_FILES).glob("**/*.*"))
    # sort according to date
    idx_mtime = 8
    files.sort(key=lambda x: x.stat()[idx_mtime])
    return files


def limit_temp_files():
    files = get_list_temp_files()
    while len(files) > MAX_NUM_TEMP_FILES:
        cleanup(files.pop(0).as_posix())


# ----- TEST FUNCTIONS
@app.get(ENTRYPOINT_TEST)
def negate(boolean: bool):
    return not boolean


@app.get(ENTRYPOINT_TEST_BASLER)
def connect_to_camera(serial_number: int = None):
    try:
        get_camera_flag = 0
        factory = pylon.TlFactory.GetInstance()
        print(f"DEBUG: pylon.TlFactory.GetInstance(): {factory}")
        print(f"DEBUG: pylon.TlFactory.GetInstance().EnumerateDevices(): {factory.EnumerateDevices()}")
        devices = list(factory.EnumerateDevices())
        if len(devices) < 1:
            print(f"DEBUG -- ERROR: no devices found!")

        if serial_number:
            for dev in devices:
                print(dev.GetModelName(), dev.GetSerialNumber())
                flag_found = dev.GetSerialNumber() == str(serial_number)
                print(f"DEBUG: dev.GetSerialNumber() == str(serial_number): "
                      f"{dev.GetSerialNumber()} == str({serial_number}): "
                      f"{flag_found}")
                if flag_found:
                    cam_info = dev
                    get_camera_flag = 1
                    break
    except:
        get_camera_flag = -1

    try:
        pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(cam_info))
        get_connection_flag = 1
    except:
        get_connection_flag = -1
    return {
        "get_camera_flag": get_camera_flag,
        "get_connection_flag": get_connection_flag
    }


@app.get(ENTRYPOINT_TEST_IMAGE)
def return_test_image(
        exposure_time_microseconds: int = None,
        serial_number: int = None,
        ip_address: str = None,
        emulate_camera: bool = False,
        timeout: int = None,
        transmission_type: str = None,
        destination_ip_address: str = None,
        destination_port: int = None,
):
    # load file
    image_path = get_env_variable("TEST_IMAGE", None)
    if image_path:
        image_path = Path(image_path)
        images = list(image_path.parent.glob(image_path.name))
        # shuffle list
        shuffle(images)
        # return first image that exists
        for p2img in images:
            if p2img.is_file():
                return FileResponse(
                    image_path.as_posix(),
                    media_type=f"image/{image_path.suffix.strip('.')}",
                    background=BackgroundTask(limit_temp_files)
                )
    # else return None
    return None


if __name__ == "__main__":
    uvicorn.run(app=app, port=5051)
