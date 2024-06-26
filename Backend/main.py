# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
import uvicorn

import numpy as np
from datetime import datetime
from pathlib import Path
from PIL import Image
import re

import logging
from timeit import default_timer
from threading import Thread

# custom packages
from plot_pil import plot_bboxs
from check_boxes import check_boxes, get_patterns_from_config
from helper_functions import image_to_base64, bytes_to_image

from utils import get_config, get_dict_from_file_or_envs, set_env_variable
from utils_data_models import build_camera_info
from utils_communication import trigger_camera, request_model_inference
from utils_fastapi import default_fastapi_setup

from DataModels import (
    SettingsMain,
    CameraPhotoParameter,
    CameraInfo,
    # ResultMain,
    OptionsReturnValuesMain,
    ResultInference,
    PatternRequest,
    Pattern
)
from typing import Union, Tuple, List, Dict, Any, Optional

set_env_variable("LOG_LEVEL", "DEBUG")  # FIXME
# get config
CONFIG = get_config()
CAMERA = build_camera_info(CONFIG)
PATTERNS, DEFAULT_PATTERN_KEY = get_patterns_from_config(CONFIG)
COLOR_MAP = get_dict_from_file_or_envs(CONFIG, "MODEL_COLOR_MAP")
CLASS_MAP = get_dict_from_file_or_envs(CONFIG, "MODEL_CLASS_MAP")

m = re.search("(?<=every\s)\d+", CONFIG["GENERAL_SAVE_IMAGES"], re.IGNORECASE)
save_every_x = int(m.group()) if m else None

# entry points
ENTRYPOINT = "/"

# create fastAPI object
title = "Backend"
summary = "Minimalistic server providing a REST api to orchestrate a containerized computer vision application."
app = default_fastapi_setup(title, summary)

# get logger
logger = logging.getLogger("uvicorn")
# initialize counter
counter = 0


@app.get(ENTRYPOINT + "main")
def main(
        camera: CameraPhotoParameter = Depends(),
        settings: SettingsMain = Depends(),
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
    logger.debug(f"Request camera: {camera_}")
    try:
        t0 = default_timer()
        # trigger camera
        img_bytes = trigger_camera(camera_, timeout=50000)
        # log execution time
        dt = default_timer() - t0
        logger.debug(f"Trigger camera took {dt * 1000:.4g} ms")

    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: trigger_camera(...). Camera not responding."
        logger.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at camera backend: {e}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    # ----- Inference backend
    bboxes = [(0, 0, 0, 0)]
    try:
        address = CONFIG["INFERENCE_URL"]
        logger.debug(f"Request model inference backend at {address}")
        t0 = default_timer()
        result: ResultInference = request_model_inference(
            address=address,
            image_raw=img_bytes,
            extension=camera_.format
        )
        bboxes, class_ids, scores = result["bboxes"], result["class_ids"], result["scores"]

        # log execution time
        dt = default_timer() - t0
        logger.debug(f"Inference took {dt * 1000:.4g} ms; # bounding-boxes={len(bboxes)}")

        # to numpy
        scores = np.asarray(scores)
        lg = scores >= settings.min_score
        scores = scores[lg].tolist()
        class_ids = np.asarray(class_ids)[lg].tolist()
        bboxes = np.asarray(bboxes)[lg].tolist()
        logging.debug(f"{sum(lg)}/{len(lg)} objects above minimum confidence score {settings.min_score}.")
    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: Inference backend not responding."
        logger.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at inference backend: {e}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)
    # TODO: draw bounding-boxes on image? => Threading
    # TODO: save images

    # img from bytes
    img = bytes_to_image(img_bytes)

    # ----- Plot bounding-boxes
    img_draw = plot_bboxs(
        img.convert("RGB"),
        bboxes,
        scores,
        class_ids,
        class_map=CLASS_MAP,
        color_map=COLOR_MAP
    )

    # ----- Check bounding-box pattern
    decision = None
    pattern_name = None
    lg = None
    pattern_key = settings.pattern_key

    note_to_saved_image = None
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
        logger.debug(f"Pattern check took {dt * 1000:.4g} ms")

        if decision:
            msg = f"Bounding-Boxes found for pattern {pattern_name}"
            logger.info(msg)
        elif pattern_name:
            msg = (f"Not all objects were found. "
                   f"Best pattern: {pattern_name} with {lg}.")
            logger.warning(msg)

        # Save image if applicable
        if CONFIG["GENERAL_SAVE_IMAGES_WITH_FAILED_PATTERN_CHECK"] and not decision:
            note_to_saved_image = "failed"
    else:
        logger.info("No pattern provided to check bounding-boxes.")

    # save image
    global counter
    if note_to_saved_image or \
            (isinstance(CONFIG["GENERAL_SAVE_IMAGES"], str) and (CONFIG["GENERAL_SAVE_IMAGES"].lower() == "all")) or \
            (save_every_x and (counter % save_every_x == 0)):
        Thread()
        Thread(target=save_image,
               args=(img,
                     camera_.format,
                     CONFIG["GENERAL_FOLDER_SAVED_IMAGES"],
                     note_to_saved_image
                     )
               ).start()

    # ----- Return
    # thread_draw.join()
    # img_draw = thread_draw_result["output"]

    content = dict()
    if return_options.decision:
        content["decision"] = decision
    if return_options.pattern_name:
        content["pattern_name"] = pattern_name
        content["pattern_lg"] = lg

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

    # increase global counter
    counter += 1
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


def save_image(img: Image, image_extension: str, folder: str = None, note: Union[str, List[str]] = None):
    if note is None:
        notes = []
    elif isinstance(note, str):
        notes = [note]
    elif isinstance(note, list):
        notes = [f"{el}" for el in note]
    else:
        raise TypeError(f"Expecting input 'note' to be a string or a list of strings but was {type(note)}.")

    # create filename from current timestamp
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_".join(notes)
    # create full path (not necessarily absolute)
    image_path = Path(folder) / filename
    # save image
    img.save(image_path.with_suffix(f".{image_extension.strip('.')}"))


if __name__ == "__main__":
    logger.debug("====> Starting uvicorn server <====")
    uvicorn.run(app=app, port=5050, log_level=logging.DEBUG)
