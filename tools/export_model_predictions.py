from pathlib import Path

import cv2
from PIL import Image
import numpy as np
import onnxruntime as ort
from tqdm import tqdm

from Inference.utils_image_cv2 import prepare_image
from determine_desired_coordinates import read_file, xyxy2xywh


if __name__ == "__main__":
    path_to_model_file = Path("../Inference/data/20240830_CRUplus_YOLOv7tiny.onnx")
    path_to_training_file = Path(r"CRU_TrnVal4pattern_L2.txt")
    path_to_images = Path(r"C:\Users\schwmax\Proj\Coding\YOLOv7_scw\dataset\CRURotorAssembly\data")
    export_dir = Path("export")

    # read file
    files = [Path(ln) for ln in read_file(path_to_training_file)]
    suffix = ".jpg"
    images = [path_to_images / f"{fl.stem}{suffix}" for fl in files]

    # initialize ONNX session
    session = ort.InferenceSession(
        path_to_model_file,
        providers=None
        # https://onnxruntime.ai/docs/execution-providers/
    )

    predictions = dict()
    for fl in tqdm(images):
        # read image
        img = Image.open(fl).convert("RGB")
        # prepare image
        img_sz = (544, 640)
        precision = "fp32"
        img_mdl = prepare_image(np.asarray(img), img_sz, precision)

        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        results = session.run(
            output_names=[output_name],
            input_feed={input_name: img_mdl}
            )

        bboxes_xyxy = results[0][:, 1:5] / (img_sz[::-1] * 2)
        class_ids = results[0][:, 5].astype(int)
        scores = results[0][:, 6]

        bboxes_xywh = np.array([xyxy2xywh(bb) for bb in bboxes_xyxy])

        predictions[fl.stem] = {"bbox": bboxes_xywh, "class_ids": class_ids, "scores": scores}

    export_dir.mkdir(exist_ok=True, parents=True)
    for ky, vl in predictions.items():
        cids = vl["class_ids"]
        bbox = vl["bbox"]
        with open((export_dir / ky).with_suffix(".txt"), "w") as fid:
            fid.writelines([f"{id} {' '.join(bb.round(5).astype(str))}\n" for id, bb in zip(cids, bbox)])
