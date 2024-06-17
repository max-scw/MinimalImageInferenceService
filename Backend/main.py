from fastapi_offline import FastAPIOffline as FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator
from pathlib import Path

import onnxruntime as ort

import logging
import sys
from timeit import default_timer

# custom packages
from utils import get_config, get_env_variable, cast_logging_level
from utils_image import scale_coordinates_to_image_size, prepare_image, image_from_bytes


# get config
CONFIG = get_config(default_prefix="")
logging.debug(f"CONFIG: {CONFIG}")
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


app = FastAPI()

# create endpoint for prometheus
Instrumentator().instrument(app).expose(app)  # produces a False in the console every time a valid entrypoint is called


# ----- home
@app.get("/")
async def home():
    return {
        "Description": "Minimal inference server"
    }


@app.post(ENTRYPOINT_INFERENCE)
async def predict(file: UploadFile = File(...)):
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    image_bytes = await file.read()

    image = image_from_bytes(image_bytes)
    # preprocess image
    img_mdl = prepare_image(image, CONFIG["MODEL_IMAGE_SIZE"], CONFIG["MODEL_PRECISION"])

    t0 = default_timer()
    input_name = ONNX_SESSION.get_inputs()[0].name
    output_name = ONNX_SESSION.get_outputs()[0].name
    results = ONNX_SESSION.run([output_name], {input_name: img_mdl})
    logging.debug(f"Inference took {(t0 - default_timer()) / 1000:.2} ms.")
    # raw output json.dumps(results[0].tolist())

    bboxes = results[0][:, 1:5]
    class_ids = results[0][:, 5]
    scores = results[0][:, 6]

    # re-scale boxes
    logging.debug(f"predict(): img_mdl.shape={img_mdl.shape}, image.shape={image.shape}")
    bboxes = scale_coordinates_to_image_size(bboxes, img_mdl.shape[2:], image.shape[:2])

    content = {
        "bboxes": bboxes.round(1).tolist(),
        "class_ids": class_ids.astype(int).tolist(),
        "scores": scores.round(3).tolist()
    }
    return JSONResponse(content=content)


if __name__ == "__main__":
    # set logging to DEBUG when called as default entry point
    logging.basicConfig(level=logging.DEBUG)

    uvicorn.run(app=app, port=5052)
