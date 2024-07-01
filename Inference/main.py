# from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path

import onnxruntime as ort

import logging
import sys
from timeit import default_timer

# custom packages
from utils import get_config, set_env_variable, get_logging_level
from utils_fastapi import default_fastapi_setup
from utils_image import scale_coordinates_to_image_size, prepare_image, image_from_bytes
from DataModels import ResultInference

# get config
CONFIG = get_config()
logging.debug(f"Configuration (CONFIG): {CONFIG}")

# get model path from config
model_path = Path(CONFIG["MODEL_FOLDER_DATA"]) / CONFIG["MODEL_FILENAME"]
path_to_model_file = model_path.with_suffix(".onnx")
logging.info(f"Loading model from {path_to_model_file} (file exists: {path_to_model_file.exists()})")

# initialize ONNX session
ONNX_SESSION = ort.InferenceSession(path_to_model_file)

# log input shapes
input_shapes = {el.name: el.shape for el in ONNX_SESSION.get_inputs()}
logging.info(f"Model input(s) {input_shapes}")

# entry points
ENTRYPOINT_INFERENCE = "/inference"

# setup of fastAPI server
title = "Minimal-ONNX-Inference-Server"
summary = "Minimalistic server providing a REST api to an ONNX session."
app = default_fastapi_setup(title, summary)


@app.post(ENTRYPOINT_INFERENCE)
async def predict(
        image: UploadFile = File(...),
        # response_model=ResultInference,
):
    logging.info(f"call {ENTRYPOINT_INFERENCE}")
    logging.getLogger().setLevel(logging.DEBUG) # FIXME
    logging.info(f"logging.level = {logging.getLogger().level}")
    if image.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    # wait for file transmission
    image_bytes = await image.read()
    img = image_from_bytes(image_bytes)
    logging.debug(f"Image received: {img.shape}")

    # preprocess image
    img_mdl = prepare_image(img, CONFIG["MODEL_IMAGE_SIZE"], CONFIG["MODEL_PRECISION"])
    logging.debug(f"Image shape, config: {CONFIG['MODEL_IMAGE_SIZE']}, prepared {img_mdl.shape}")

    t0 = default_timer()
    input_name = ONNX_SESSION.get_inputs()[0].name
    output_name = ONNX_SESSION.get_outputs()[0].name
    results = ONNX_SESSION.run([output_name], {input_name: img_mdl})
    logging.debug(f"Inference took {(default_timer() - t0) / 1000:.2g} ms.")

    logging.debug(f"len(results)={len(results)}; results[0].shape={results[0].shape}")

    bboxes = results[0][:, 1:5]
    class_ids = results[0][:, 5]
    scores = results[0][:, 6]

    # re-scale boxes
    logging.debug(f"Rescale boxes to original image size: img_mdl.shape={img_mdl.shape}, img.shape={img.shape}")
    bboxes = scale_coordinates_to_image_size(bboxes, img_mdl.shape[2:], img.shape[:2])

    content = {
        "bboxes": bboxes.round(1).tolist(),
        "class_ids": class_ids.astype(int).tolist(),
        "scores": scores.round(3).tolist()
    }
    return JSONResponse(content=content)


if __name__ == "__main__":
    log_level = get_logging_level(default=logging.DEBUG)
    print(f"Logging level: {log_level}")
    # get logger
    logger = logging.getLogger("uvicorn")
    logger.setLevel(log_level)
    logger.debug("====> Starting uvicorn server <====")
    logger.debug(f"logger.level = {logger.level}")
    uvicorn.run(app=app, port=5052, log_level=log_level)
