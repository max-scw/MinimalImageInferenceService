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
from utils import get_config, set_env_variable
from utils_fastapi import default_fastapi_setup
from utils_image import scale_coordinates_to_image_size, prepare_image, image_from_bytes


# get config
CONFIG = get_config()

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


title = "Minimal-ONNX-Inference-Server"
summary = "Minimalistic server providing a REST api to an ONNX session."
app = default_fastapi_setup(title, summary)


@app.post(ENTRYPOINT_INFERENCE)
async def predict(
        file: UploadFile = File(...)
):
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    # wait for file transmission
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

    uvicorn.run(app=app, port=5052)
