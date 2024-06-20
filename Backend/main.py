# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
import uvicorn

import logging
from timeit import default_timer
from threading import Thread

# custom packages
from plot_pil import plot_bboxs
from check_boxes import check_boxes, get_patterns_from_config
from helper_functions import image_to_base64, bytes_to_image

from utils import get_config
from utils_data_models import build_camera_info
from utils_communication import trigger_camera, request_model_inference
from utils_fastapi import default_fastapi_setup

from DataModels import (
    CameraParameter,
    CameraPhotoParameter,
    CameraInfo,
    # ResultMain,
    OptionsReturnValuesMain,
    ResultInference,
    PatternRequest,
    Pattern
)
from typing import Union, Tuple, List, Dict, Any, Optional


# get config
CONFIG = get_config()
CAMERA = build_camera_info(CONFIG)
PATTERNS, DEFAULT_PATTERN_KEY = get_patterns_from_config(CONFIG)

# entry points
ENTRYPOINT = "/"

# create fastAPI object
title = "Backend"
summary = "Minimalistic server providing a REST api to orchestrate a containerized computer vision application."
app = default_fastapi_setup(title, summary)


@app.get(ENTRYPOINT + "main")
def main(
        camera: CameraPhotoParameter = Depends(),
        pattern_key: Optional[str] = None,
        return_options: OptionsReturnValuesMain = Depends()
):
    # create local CameraInfo instance
    camera_ = CameraInfo(url=CAMERA.url, **camera.dict())
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
    bboxes = [(0, 0, 0, 0)]
    try:
        address = CONFIG["INFERENCE_URL"]
        logging.debug(f"Request model inference backend at {address}")
        t0 = default_timer()
        result: ResultInference = request_model_inference(
            address=address,
            image_raw=img_bytes,
            extension=camera_.format
        )
        bboxes, class_ids, scores = result["bboxes"], result["class_ids"], result["scores"]

        # log execution time
        dt = default_timer() - t0
        logging.debug(f"Inference took {dt * 1000:.4g} ms; # bounding-boxes={len(bboxes)}")

    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: Inference backend not responding."
        logging.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at inference backend: {e}"
        logging.error(msg)
        raise HTTPException(status_code=400, detail=msg)
    # TODO: draw bounding-boxes on image? => Threading

    # img from bytes
    img = bytes_to_image(img_bytes)

    class_map = None
    color_map = None

    # ----- Plot bounding-boxes
    img_draw = plot_bboxs(
        img.convert("RGB"),
        bboxes,
        scores,
        class_ids,
        class_map=class_map,
        color_map=color_map
    )

    # ----- Check bounding-box pattern
    decision = None
    pattern_name = None
    if pattern_key is None:
        pattern_key = DEFAULT_PATTERN_KEY

    if pattern_key:
        t0 = default_timer()
        decision, pattern_name, lg = _check_pattern(
            bboxes,
            class_ids,
            PATTERNS[pattern_key]
        )
        # log execution time
        dt = default_timer() - t0
        logging.debug(f"Pattern check took {dt * 1000:.4g} ms")

        if decision:
            msg = f"Bounding-Boxes found for pattern {pattern_name}"
            logging.info(msg)
        elif pattern_name:
            msg = (f"Not all objects were found. "
                   f"Best pattern: {pattern_name} with {lg}.")
            logging.warning(msg)
    else:
        logging.info("No pattern provided to check bounding-boxes.")

    # ----- Return
    # thread_draw.join()
    # img_draw = thread_draw_result["output"]

    content = dict()
    if return_options.decision:
        content["decision"] = decision
    if return_options.pattern_name:
        content["pattern_name"] = pattern_name

    if return_options.img or return_options.img_drawn:
        content["images"] = dict()
        if return_options.img:
            content["images"]["img"] = image_to_base64(img)
        if return_options.img_drawn:
            content["images"]["img_drawn"] = image_to_base64(img_draw)

    if return_options.bboxes or return_options.class_ids or return_options.scores:
        content["results"] = dict()
        if return_options.bboxes:
            content["results"]["bboxes"] = bboxes
        if return_options.class_ids:
            content["results"]["class_ids"] = class_ids
        if return_options.scores:
            content["results"]["scores"] = scores

    return JSONResponse(content=content)


@app.post(ENTRYPOINT + "check-pattern")
async def check_pattern(request: PatternRequest):
    bboxes = request.coordinates
    class_ids = request.class_ids
    # patterns to check against
    keyword = request.pattern_key.lower() if request.pattern_key else DEFAULT_PATTERN_KEY

    if keyword is None:
        keyword = DEFAULT_PATTERN_KEY
    if request.pattern is None:
        pattern = PATTERNS[keyword]
    else:
        pattern = request.pattern

    decision, pattern_name, lg = _check_pattern(
        bboxes,
        class_ids,
        pattern=pattern
    )

    return JSONResponse(content={
        "decision": decision,
        "pattern_name": pattern_name,
        "lg": lg,
    })


def _check_pattern(
        # bounding boxes: coordinates and classes
        bboxes: List[Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]],
        class_ids: List[int],
        # pattern to check against
        pattern: Union[Pattern, Dict[str, Pattern]]
):
    t0 = default_timer()
    pattern_name, lg = check_boxes(bboxes, class_ids, pattern)
    dt = default_timer() - t0

    logging.debug(f"check_boxes(): pattern_name={pattern_name}, lg={lg}; took {dt:.4g} s")

    # output
    decision = (len(lg) > 1) and all(lg)
    return decision, pattern_name, lg


if __name__ == "__main__":

    uvicorn.run(app=app, port=5050, log_level=logging.DEBUG)
