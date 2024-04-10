from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

import onnxruntime as ort

import logging
from pathlib import Path


from utils import get_config
from utils_image import scale_coordinates_to_image_size, prepare_image, image_from_bytes


CONFIG = get_config(default_prefix="")
model_path = Path(CONFIG["MODEL_FOLDER_DATA"]) / CONFIG["MODEL_FILENAME"]
path_to_model_file = model_path.with_suffix(".onnx")
msg = f"Loading model from {path_to_model_file} (file exists: {path_to_model_file.exists()})"
logging.info(msg)
print("INFO " + msg)
ONNX_SESSION = ort.InferenceSession(path_to_model_file)


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

    input_name = ONNX_SESSION.get_inputs()[0].name
    output_name = ONNX_SESSION.get_outputs()[0].name
    results = ONNX_SESSION.run([output_name], {input_name: img_mdl})

    bboxes = results[0][:, 1:5]
    class_ids = results[0][:, 5]
    scores = results[0][:, 6]

    # re-scale boxes
    msg = f"predict(): img_mdl.shape={img_mdl.shape}, image.shape={image.shape}"
    logging.debug(msg)
    print("DEBUG " + msg)
    bboxes = scale_coordinates_to_image_size(bboxes, img_mdl.shape[2:], image.shape[:2])

    content = {
        "bboxes": bboxes.round(1).tolist(),
        "class_ids": class_ids.astype(int).tolist(),
        "scores": scores.round(3).tolist()
    }
    return JSONResponse(content=content)


if __name__ == "__main__":
    uvicorn.run(app=app, port=5050)
