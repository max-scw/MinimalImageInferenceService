# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

# import requests
from utils_communication import trigger_camera, request_model_inference
from utils_fastapi import default_fastapi_setup
from DataModels import CameraInfo, InferenceInfo


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


@app.post(ENTRYPOINT)
async def main(
        camera: CameraInfo,
        # inference: InferenceInfo,
        # file: UploadFile = File(...)
):
    # TODO: update all data models with info sent with

    # ----- Camera
    logging.debug(f"Request camera at {camera.url}")
    try:
        img_bytes = trigger_camera(camera, timeout=50000)
    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: trigger_camera(...). Camera not responding."
        logging.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at camera backend: {e}"
        logging.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    # ----- Inference backend
    logging.debug(f"Request model inference backend at {CONFIG['INFERENCE_URL']}")
    try:
        result = request_model_inference(
            address=CONFIG["INFERENCE_URL"],
            image_raw=img_bytes,
            extension=CAMERA.image_extension
        )
        logging.debug(f"main(): {result} = request_model_inference(...)")
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

    return StreamingResponse(
        img_bytes,
        media_type="image/jpeg",
        headers={"content": str(content)}
    )


if __name__ == "__main__":
    # set logging to DEBUG when called as default entry point
    logging.basicConfig(level=logging.DEBUG)

    uvicorn.run(app=app, port=5050)
