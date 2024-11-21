# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import Counter, Gauge

from pathlib import Path
import numpy as np

import onnxruntime as ort

from timeit import default_timer

# custom packages
from utils import get_config, setup_logging, set_env_variable, default_from_env
from utils_fastapi import (
    default_fastapi_setup,
    setup_prometheus_metrics,
    AccessToken
)
from utils_image_cv2 import (
    scale_coordinates_to_image_size,
    prepare_image, bytes_to_image_array
)
# from utils_image import bytes_to_image_pil

# Setup logging
logger = setup_logging(__name__)

# get config
CONFIG = get_config()
logger.debug(f"Configuration (CONFIG): {CONFIG}")

# get model path from config
model_path = Path(CONFIG["MODEL_FOLDER_DATA"]) / CONFIG["MODEL_FILENAME"]
path_to_model_file = model_path.with_suffix(".onnx")
logger.info(f"Loading model from {path_to_model_file} (file exists: {path_to_model_file.exists()})")

# initialize ONNX session
ONNX_SESSION = ort.InferenceSession(
    path_to_model_file,
    providers=CONFIG["ONNX_PROVIDERS"] if "ONNX_PROVIDERS" in CONFIG else None
    # https://onnxruntime.ai/docs/execution-providers/
)

# log input shapes
input_shapes = {el.name: el.shape for el in ONNX_SESSION.get_inputs()}
logger.debug(f"Model input(s) {input_shapes}")

# entry points
ENTRYPOINT_INFERENCE = "/inference"

# setup of fastAPI server
title = "Minimal-ONNX-Inference-Server"
summary = "Minimalistic server providing a REST api to an ONNX session."
app = default_fastapi_setup(title, summary)

# set up /metrics endpoint for prometheus
EXECUTION_COUNTER, EXCEPTION_COUNTER, EXECUTION_TIMING = setup_prometheus_metrics(
    app,
    entrypoints_to_track=[ENTRYPOINT_INFERENCE]
)
# additional custom metrics
RESULTS = dict()  # initialize with empty dictionary
EXECUTION_TIMING["onnx"] = Gauge(
    name="ONNX_session_execution_time",
    documentation=f"How long did the actual ONNX session call took?"
)


def postprocess(
        results,
        th_score
):
    # YOLOv7 results[0].shape = (1, 30, 7) ... [batch, # boxes, (nr batch, x, y, x, y, cls, score)]
    # YOLOv10n results[0].shape = (1, 300, 6) ... [batch, # boxes, (x, y, x, y, score, cls)]
    batch_i = results[0]
    if batch_i.shape[1] > 6:
        # YOLOv10
        idx_xyxy = 0
        idx_cls = 5
        idx_score = 4
        batch_i = batch_i[0]
    else:
        # YOLOv7
        idx_xyxy = 1
        idx_cls = 5
        idx_score = 6

    bboxes_xyxy = batch_i[:, idx_xyxy:(idx_xyxy + 4)]
    class_ids = batch_i[:, idx_cls].astype(int)
    scores = batch_i[:, idx_score]

    lg = scores > th_score
    return bboxes_xyxy[lg, :], class_ids[lg], scores[lg]


@app.post(ENTRYPOINT_INFERENCE)
# Decorators do not work for async functions
async def predict(image: UploadFile = File(...), token = AccessToken):
    t0 = default_timer()
    logger.debug(f"call {ENTRYPOINT_INFERENCE}")
    # increment counter for /metrics endpoint
    EXECUTION_COUNTER[ENTRYPOINT_INFERENCE].inc()

    with EXCEPTION_COUNTER[ENTRYPOINT_INFERENCE].count_exceptions() and EXECUTION_TIMING[ENTRYPOINT_INFERENCE].time():
        if image.content_type.split("/")[0] != "image":
            raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

        # wait for file transmission
        image_bytes = await image.read()
        img = bytes_to_image_array(image_bytes)
        logger.debug(f"Image received: {img.shape}")

        # preprocess image
        img_mdl = prepare_image(img, CONFIG["MODEL_IMAGE_SIZE"], CONFIG["MODEL_PRECISION"])
        logger.debug(f"Image shape, config: {CONFIG['MODEL_IMAGE_SIZE']}, prepared {img_mdl.shape}")

        t1 = default_timer()
        input_name = ONNX_SESSION.get_inputs()[0].name
        output_name = ONNX_SESSION.get_outputs()[0].name
        with EXECUTION_TIMING["onnx"].time():
            results = ONNX_SESSION.run(
                output_names=[output_name],
                input_feed={input_name: img_mdl}
            )
        logger.debug(f"Inference took {(default_timer() - t1) / 1000:.3g} ms.")

        logger.debug(f"len(results)={len(results)}; results[0].shape={results[0].shape}")

        bboxes, class_ids, scores = postprocess(results, CONFIG["MODEL_TH_SCORE"])

        # re-scale boxes
        logger.debug(f"Rescale boxes to original image size: img_mdl.shape={img_mdl.shape}, img.shape={img.shape}")
        bboxes = scale_coordinates_to_image_size(bboxes, img_mdl.shape[2:], img.shape[:2])

        # update metrics
        for cls in class_ids:
            if cls not in RESULTS:
                # initialize on the fly
                RESULTS[cls] = {
                    "counter": Counter(
                        name=f"class_{cls}_predictions",
                        documentation=f"Counts how often class {cls} is predicted."
                    ),
                    "score_max": Gauge(
                        name=f"class_{cls}_score_max",
                        documentation=f"Maximum score for class {cls} on latest input."
                    ),
                    "score_min": Gauge(
                        name=f"class_{cls}_score_min",
                        documentation=f"Minium score for class {cls} on latest input."
                    )
                }
            # increment counter
            RESULTS[cls]["counter"].inc()

        for cls in np.unique(class_ids):
            # slice scores
            lg = class_ids == cls
            RESULTS[cls]["score_max"].set(scores[lg].max())
            RESULTS[cls]["score_min"].set(scores[lg].min())

        # package return values
        content = {
            "bboxes": bboxes.round(1).tolist(),
            "class_ids": class_ids.tolist(),
            "scores": scores.round(3).tolist()
        }
        logger.debug(f"Calling {ENTRYPOINT_INFERENCE} took {(default_timer() - t0) / 1000:.3g} ms.")
    return JSONResponse(content=content)


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=5052,
        host="0.0.0.0",
        access_log=True,
        log_config=None,  # Uses the logging configuration in the application
        ssl_keyfile=default_from_env("SSL_KEYFILE", None),  # "server.key"
        ssl_certfile=default_from_env("SSL_CERTIFICATE", None),  # "server.crt"
    )
