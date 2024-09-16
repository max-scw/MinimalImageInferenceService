from pathlib import Path

from PIL import Image
import numpy as np
import onnxruntime as ort
from tqdm import tqdm

from typing import Union, List

from Inference.utils_image_cv2 import prepare_image
from determine_desired_coordinates import read_file, xyxy2xywh
from Backend.plot_pil import plot_bboxs


class PredictONNXModel:
    def __init__(
            self,
            path_to_model: Union[str, Path],
            img_sz=(544, 640),
            precision="fp32"
    ):
        self.img_sz = img_sz
        self.precision = precision

        # initialize ONNX session
        self.session = ort.InferenceSession(
            path_to_model,
            providers=None
            # https://onnxruntime.ai/docs/execution-providers/
        )

    def predict(self, image: Image):
        img_mdl = prepare_image(np.asarray(image), self.img_sz, self.precision)

        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name
        results = self.session.run(
            output_names=[output_name],
            input_feed={input_name: img_mdl}
        )

        bboxes_xyxy = results[0][:, 1:5] / (self.img_sz[::-1] * 2)
        class_ids = results[0][:, 5].astype(int)
        scores = results[0][:, 6]

        return bboxes_xyxy, class_ids, scores


if __name__ == "__main__":
    path_to_model_file = Path("../Inference/data/20240905_CRUplus_crop_YOLOv7tiny.onnx")
    path_to_training_file = Path(r"CRU_TrnVal4pattern_OGL_L1.txt")
    path_to_images = Path(r"C:\Users\schwmax\OneDrive - Voith Group of Companies\ProductionDataArchive\ImageData\RotorAssembly\data\img")
    export_dir = Path("export_crop")

    # read file
    files = [Path(ln) for ln in read_file(path_to_training_file)]
    suffix = ".jpg"
    images = [path_to_images / f"{fl.stem}{suffix}" for fl in files]

    model = PredictONNXModel(path_to_model_file, (544, 640), "fp32")

    predictions = dict()
    for fl in tqdm(images):
        # read image
        img = Image.open(fl).convert("RGB")

        bboxes_xyxy, class_ids, scores = model.predict(img)

        bboxes_xywh = np.array([xyxy2xywh(bb) for bb in bboxes_xyxy])

        # plot image
        img_bbox = plot_bboxs(
            img,
            bbox=(bboxes_xyxy * (img.size * 2)).round().astype(int).tolist(),
            scores=scores,
            classes=class_ids,
            line_thickness=3
        )
        export_dir.mkdir(exist_ok=True, parents=True)
        img_bbox.save(export_dir / f"{fl.stem}.jpg")
        # store info
        predictions[fl.stem] = {"bbox": bboxes_xywh, "class_ids": class_ids, "scores": scores}

    export_dir.mkdir(exist_ok=True, parents=True)
    for ky, vl in predictions.items():
        cids = vl["class_ids"]
        bbox = vl["bbox"]
        with open((export_dir / ky).with_suffix(".txt"), "w") as fid:
            fid.writelines([f"{id} {' '.join(bb.round(5).astype(str))}\n" for id, bb in zip(cids, bbox)])
