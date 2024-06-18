# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
import uvicorn

# import requests
from utils_communication import trigger_camera, request_model_inference
from utils_fastapi import default_fastapi_setup
from DataModels import CameraParameter, CameraInfo, InferenceInfo


import logging
from timeit import default_timer

# custom packages
from utils import get_config
from utils_data_models import build_camera_info


# get config
CONFIG = get_config()
CAMERA = build_camera_info(CONFIG)

# entry points
ENTRYPOINT = "/"

# create fastAPI object
title = "Backend"
summary = "Minimalistic server providing a REST api to orchestrate a containerized computer vision application."
app = default_fastapi_setup(title, summary)


@app.get(ENTRYPOINT + "main")
def main(
        camera: CameraParameter = Depends(),
        # inference: InferenceInfo,
        # file: UploadFile = File(...)
):
    # create local CameraInfo instance
    camera_ = CameraInfo(camera=camera)
    # update missing fields
    for attr in CAMERA.__fields__:
        value = getattr(CAMERA, attr)
        if not hasattr(camera_, attr):
            setattr(camera_, attr, value)

    # ----- Camera
    logging.debug(f"Request camera: {camera_}")
    try:
        t0 = default_timer()
        # trigger camera
        img_bytes = trigger_camera(camera_, timeout=50000)
        # log execution time
        dt = default_timer() - t0
        logging.debug(f"Trigger camera took {dt * 1000:.4g} ms")

    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: trigger_camera(...). Camera not responding."
        logging.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at camera backend: {e}"
        logging.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    # ----- Inference backend
    try:
        address = CONFIG["INFERENCE_URL"]
        logging.debug(f"Request model inference backend at {address}")
        t0 = default_timer()
        result = request_model_inference(
            address=address,
            image_raw=img_bytes,
            extension=CAMERA.image_extension
        )
        # log execution time
        dt = default_timer() - t0
        logging.debug(f"Inference took {dt * 1000:.4g} ms; result={result}")

    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: request_model_inference(...). Inference backend not responding."
        logging.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at inference backend: {e}"
        logging.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    # TODO: draw bounding-boxes on image?

    # ----- Check bounding-box pattern
    # TODO: check bounding box pattern
    logging.debug(f"Request pattern checker at {CONFIG['PATTERN_CHECKER_URL']}")
    t0 = default_timer()
    # log execution time
    dt = default_timer() - t0
    logging.debug(f"Pattern check took {dt * 1000:.4g} ms")
    # TODO write wrapper for the request
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

    # ----- Return
    content = {
        "decision": True if decision else False,
        **result,
    }

    return Response(
        content=img_bytes,
        media_type=f"image/{CAMERA.image_extension.strip('.')}",
        headers={"content": str(content)}
    )


if __name__ == "__main__":

    uvicorn.run(app=app, port=5050)
