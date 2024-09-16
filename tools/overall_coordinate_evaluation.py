from pathlib import Path
from tqdm import tqdm
from PIL import Image
import numpy as np

from export_model_predictions import PredictONNXModel
from determine_desired_coordinates import read_file, read_label

from Backend.check_boxes import check_boxes, load_patterns, xywh2xyxy, xyxy2xywh
from Backend.plot_pil import plot_bboxs, plot_bounds


if __name__ == "__main__":
    path_to_model_file = Path("../Inference/data/20240905_CRUplus_crop_YOLOv7tiny.onnx")
    path_to_images = Path(r"C:\Users\schwmax\OneDrive - Voith Group of Companies\ProductionDataArchive\ImageData\RotorAssembly\data") / "CRU_2_Val.txt"
    path_to_pattern = Path("./desired_coordinates_20240905_CRUplus_crop_YOLOv7tiny_rotated180.yml")
    export_dir = Path("./export_dir")

    # read file
    files = [Path(ln) for ln in read_file(path_to_images)]
    suffix = ".jpg"
    images = [path_to_images.parent / fl.with_suffix(suffix) for fl in files]

    # read pattern
    pattern = load_patterns(path_to_pattern)[path_to_pattern.stem]

    # create ONNX model session
    model = PredictONNXModel(path_to_model_file, (544, 640), "fp32")

    correct = []
    for fl in tqdm(images):
        # read image
        img = Image.open(fl).convert("RGB")
        # predict bounding boxes
        bboxes_xyxy, class_ids, scores = model.predict(img)
        # check pattern
        pattern_name, lg = check_boxes(bboxes_xyxy, class_ids, pattern)
        # overall decision
        decision = (len(lg) > 1) and all(lg)

        # determine expectation
        # read label
        label = read_label(fl.with_suffix(".txt"))
        class_ids_lb = label[:, 0]
        bboxes_xywh_lb = label[:, 1:]
        bboxes_xyxy_lb = xywh2xyxy(bboxes_xywh_lb)
        # check pattern
        pattern_name_lb, lg_lb = check_boxes(bboxes_xyxy_lb, class_ids_lb, pattern)
        # overall decision
        decision_lb = (len(lg_lb) > 1) and all(lg_lb)
        if decision_lb:
            print(fl)

        correct.append(decision == decision_lb)

        if decision != decision_lb:
            bboxes_xywh = np.array(xyxy2xywh(bboxes_xyxy))

            # plot image
            img_bbox = plot_bboxs(
                img,
                bbox=(bboxes_xyxy * (img.size * 2)).round().astype(int).tolist(),
                scores=scores,
                classes=class_ids,
                line_thickness=3
            )

            pat_failed = [vl for ky, vl in zip(lg, pattern[pattern_name]) if not ky]
            img_draw = plot_bounds(img_bbox, pat_failed)

            img_draw.save(export_dir / f"{fl.stem}.jpg")