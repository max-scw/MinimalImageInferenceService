# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import Counter, Gauge

from pathlib import Path

import onnxruntime as ort

from timeit import default_timer

# custom packages
from utils import get_config, setup_logging
from utils_fastapi import default_fastapi_setup, setup_prometheus_metrics
from utils_image import scale_coordinates_to_image_size, prepare_image, image_from_bytes

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
EXECUTION_COUNTER, EXECUTION_TIMING = setup_prometheus_metrics(
    app,
    entrypoints_to_track=[ENTRYPOINT_INFERENCE]
)
# additional custom metrics
RESULTS = dict()  # initialize with empty dictionary


@app.post(ENTRYPOINT_INFERENCE)
@EXECUTION_TIMING[ENTRYPOINT_INFERENCE].time()
async def predict(image: UploadFile = File(...)):
    logger.debug(f"call {ENTRYPOINT_INFERENCE}")
    # increment counter for /metrics endpoint
    EXECUTION_COUNTER[ENTRYPOINT_INFERENCE].inc()

    if image.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    # wait for file transmission
    image_bytes = await image.read()
    img = image_from_bytes(image_bytes)
    logger.debug(f"Image received: {img.shape}")

    # preprocess image
    img_mdl = prepare_image(img, CONFIG["MODEL_IMAGE_SIZE"], CONFIG["MODEL_PRECISION"])
    logger.debug(f"Image shape, config: {CONFIG['MODEL_IMAGE_SIZE']}, prepared {img_mdl.shape}")

    t0 = default_timer()
    input_name = ONNX_SESSION.get_inputs()[0].name
    output_name = ONNX_SESSION.get_outputs()[0].name
    results = ONNX_SESSION.run(
        output_names=[output_name],
        input_feed={input_name: img_mdl}
    )
    logger.debug(f"Inference took {(default_timer() - t0) / 1000:.2g} ms.")

    logger.debug(f"len(results)={len(results)}; results[0].shape={results[0].shape}")

    bboxes = results[0][:, 1:5]
    class_ids = results[0][:, 5].astype(int)
    scores = results[0][:, 6]

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

    for cls in class_ids.uniuqe():
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
    return JSONResponse(content=content)


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=5052,
        access_log=True,
        log_config=None  # Uses the logging configuration in the application
    )
