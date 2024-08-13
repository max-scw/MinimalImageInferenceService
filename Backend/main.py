# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
import uvicorn

import numpy as np
from pathlib import Path
import re


import logging
from timeit import default_timer
from threading import Thread

# custom packages
from plot_pil import plot_bboxs
from check_boxes import check_boxes, get_patterns_from_config
from utils_image import image_to_base64, bytes_to_image, save_image

from utils import get_config, read_mappings_from_csv, setup_logging

from utils_communication import trigger_camera, request_model_inference
from utils_fastapi import default_fastapi_setup

from DataModels import (
    SettingsMain,
    CameraInfo,
    OptionsReturnValuesMain,
    ResultInference,
    PatternRequest,
    Pattern,
)
from DataModels_BaslerCameraAdapter import (
    PhotoParams,
    BaslerCameraSettings,
    get_not_none_values
)


from typing import Union, Tuple, List, Dict, Any, Optional

# Setup logging
logger = setup_logging(__name__)

# get config
CONFIG = get_config()
logger.debug(f"Configuration (CONFIG): {CONFIG}")

# get patterns to check the model prediction
PATTERNS, DEFAULT_PATTERN_KEY = get_patterns_from_config(CONFIG)
# naming & colors for the (predicted) classes
path_to_mapping = Path(CONFIG["MODEL_FOLDER_HEAD"]) / CONFIG["MODEL_FOLDER_DATA"] / (CONFIG["MODEL_MAPPINGS"] if "MODEL_MAPPINGS" in CONFIG else "")
logger.debug(f"path_to_mapping={path_to_mapping}")
CLASS_MAP, COLOR_MAP = read_mappings_from_csv(path_to_mapping)

logger.debug(f"Default pattern key: {DEFAULT_PATTERN_KEY}, mapping classes: {CLASS_MAP}, mapping colors: {COLOR_MAP}")

m = re.search("(?<=every\s)\d+", CONFIG["GENERAL_SAVE_IMAGES"], re.IGNORECASE)
save_every_x = int(m.group()) if m else None

# entry points
ENTRYPOINT = "/"

# create fastAPI object
title = "Backend"
summary = "Minimalistic server providing a REST api to orchestrate a containerized computer vision application."
app = default_fastapi_setup(title, summary)

# initialize counter
counter = 0


@app.get(ENTRYPOINT + "main")
def main(
        camera_params: BaslerCameraSettings = Depends(),
        photo_params: PhotoParams = Depends(),
        settings: SettingsMain = Depends(),
        return_options: OptionsReturnValuesMain = Depends()
):
    t0 = default_timer()
    # create local CameraInfo instance
    camera_ = CameraInfo(url=CONFIG["CAMERA_URL"], **camera_params.dict())

    t1 = default_timer()
    logger.debug(f"CameraInfo object built: {camera_} (took {(t1 - t0) * 1000:.4g} ms)")

    # ----- Camera
    try:
        # trigger camera
        img_bytes = trigger_camera(camera_, photo_params, timeout=1000)  # FIXME: adjust timeout

        # log execution time
        t2 = default_timer()
        logger.debug(f"Trigger camera took {(t2 - t1) * 1000:.4g} ms")

    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: trigger_camera(...). Camera not responding."
        logger.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at camera backend: {e}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    t3 = default_timer()
    # ----- Inference backend
    bboxes, scores, class_ids = [(0, 0, 0, 0)], [0], [0]  # initialize default values
    try:
        address = CONFIG["INFERENCE_URL"]
        if address:
            logger.debug(f"Request model inference backend at {address}")
            result: ResultInference = request_model_inference(
                address=address,
                image_raw=img_bytes,
                extension=photo_params.format
            )
            bboxes, class_ids, scores = result["bboxes"], result["class_ids"], result["scores"]

            # log execution time
            t4 = default_timer()
            logger.debug(f"Inference took {(t4 - t3) * 1000:.4g} ms; # bounding-boxes={len(bboxes)}")

            # to numpy
            scores = np.asarray(scores)
            lg = scores >= settings.min_score
            scores = scores[lg].tolist()
            class_ids = np.asarray(class_ids)[lg].tolist()
            bboxes = np.asarray(bboxes)[lg].tolist()
            t5 = default_timer()
            logger.debug(f"{sum(lg)}/{len(lg)} objects above minimum confidence score {settings.min_score} (took {(t5 - t4) * 1000:.4g} ms).")
    except (TimeoutError, ConnectionError):
        msg = "TimeoutError: Inference backend not responding."
        logger.error(msg)
        raise HTTPException(status_code=408, detail=msg)
    except Exception as e:
        msg = f"Fatal error at inference backend: {e}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=msg)

    # TODO: draw bounding-boxes on image? => Threading
    t6 = default_timer()

    # img from bytes
    img = bytes_to_image(img_bytes)
    t7 = default_timer()
    logger.debug(f"Image object from bytes took {(t7 - t6) * 1000:.4g} ms")

    # ----- Plot bounding-boxes
    img_draw = plot_bboxs(
        img.convert("RGB"),
        bboxes,
        scores,
        class_ids,
        class_map=CLASS_MAP,
        color_map=COLOR_MAP
    )
    # log execution time
    t8 = default_timer()
    logger.debug(f"Plot bounding boxes took {(t8 - t7) * 1000:.4g} ms")

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
    t9 = default_timer()
    logger.debug(f"Pattern check took {(t9 - t8) * 1000:.4g} ms")

    # save image
    global counter
    if note_to_saved_image or \
            (isinstance(CONFIG["GENERAL_SAVE_IMAGES"], str) and (CONFIG["GENERAL_SAVE_IMAGES"].lower() == "all")) or \
            (save_every_x and (counter % save_every_x == 0)):
        # start thread to save the image
        Thread(target=save_image,
               args=(
                   img,
                   photo_params.format,
                   CONFIG["GENERAL_FOLDER_SAVED_IMAGES"],
                   note_to_saved_image
               )
               ).start()
    t10 = default_timer()
    logger.debug(f"Starting thread to save image took {(t10 - t9) * 1000:.4g} ms")

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

    t11 = default_timer()
    logger.debug(f"Building response took {(t11 - t10) * 1000:.4g} ms")

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


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=5050,
        access_log=True,
        log_config=None  # Uses the logging configuration in the application
    )
