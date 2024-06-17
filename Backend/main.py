from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

import requests
from utils_communication import trigger_camera, request_model_inference
from DataModels import CameraInfo


import logging
from timeit import default_timer

# custom packages
from utils import get_config, get_env_variable, cast_logging_level


# get config
CONFIG = get_config(default_prefix="")

# entry points
ENTRYPOINT = "/"

# create fastAPI object
summary = "Minimalistic server providing a REST api to orchestrate a containerized computer vision application."
app = FastAPI()

# create endpoint for prometheus
Instrumentator().instrument(app).expose(app)  # produces a False in the console every time a valid entrypoint is called


# ----- home
@app.get("/")
async def home():
    return {
        "Description": summary
    }



@app.post(ENTRYPOINT)
async def main(

        file: UploadFile = File(...)
):
    # TODO: update all data models with info sent with

    image_bytes = await file.read()

    # trigger camera
    try:
        img_raw = trigger_camera(camera_info, timeout=50000)
    except (TimeoutError, ConnectionError):
        logging.error("TimeoutError: trigger_camera(...). Camera not responding.")
        # TODO: HTTPS response with error code

    msg = f"main(): request_model_inference({inference_info.url}, image_raw={image.size}, extension={camera_info.image_extension})"
    logging.debug(msg)
    try:
        result = request_model_inference(
            address=inference_info.url,
            image_raw=image_bytes,
            extension=camera_info.image_extension
        )
        logging.debug(f"main(): {result} = request_model_inference(...)")
    except (TimeoutError, ConnectionError):
        logging.error("TimeoutError: request_model_inference(...). Backend not responding.")


    # TODO: check bounding box pattern
    decision = None
    pattern_name = None
    if decision:
        msg = f"Bounding-Boxes found for pattern {pattern_name}"
        logging.info(msg)
    elif pattern_name:
        msg = (f"Not all objects were found. "
               f"Best pattern: {pattern_name} with {None}.")
        logging.warning(msg)
    else:
        logging.info("No pattern provided to check bounding-boxes.")

    # output
    content = {
        "decision": True if decision else False,
        "bboxes": None,
        "classes": None,
        "scores": None,
        "image": img_raw,
    }

    return JSONResponse(content=content)


if __name__ == "__main__":
    # set logging to DEBUG when called as default entry point
    logging.basicConfig(level=logging.DEBUG)

    uvicorn.run(app=app, port=5050)
