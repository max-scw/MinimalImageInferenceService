from pathlib import Path
import numpy as np
import yaml

from sklearn.cluster import KMeans

from PIL import Image, ImageDraw
from matplotlib import pyplot as plt

from typing import List, Tuple, Union, Dict


from Backend.plot_pil import plot_one_box
from tools.utils.bboxes import xywh2xyxy, xyxy2xywh


def read_file(path_to_file: Path, suffix: str = None) -> list:
    if suffix:
        path_to_file = Path(path_to_file).with_suffix(suffix.strip("."))

    content = []
    if Path(path_to_file).exists():
        with open(path_to_file, "r") as fid:
            lines = fid.readlines()
        content = [ln.strip() for ln in lines if len(ln) > 5]
    return content


def read_label(path_to_file: Path, suffix: str = None):
    content = read_file(path_to_file, suffix)
    # cast labels to numerics
    return np.asarray([el.split(" ") for el in content], dtype=float)



def prepare_labels(
        path_to_file: Path,
        filtered_classes: List[int] = None
) -> (np.ndarray, int):
    # read file
    files_ogl = [Path(ln) for ln in read_file(path_to_file)]

    # cast to numeric
    labels = [read_label(fl) for fl in files_ogl if fl.exists()]
    n_clusters = max([len(el) for el in labels])
    print(f"Using {n_clusters} clusters.")
    # flatten to get a list of data points
    points_ogl = np.vstack(labels)

    # filter classes
    if filtered_classes:
        lg = [el in filtered_classes for el in points_ogl[:, 0]]
        points = points_ogl[lg]
    return points, n_clusters


def determine_desired_coordinates(
        path_to_predictions: Path,
        path_to_reference: Path,
        factor_std: Union[float, Dict[int, float]] = 3,
        path_to_images: Path = None,
        filtered_classes: List[int] = None
):

    points_ogl, n_clusters = prepare_labels(path_to_reference, filtered_classes)
    points_prd, _ = prepare_labels(path_to_predictions, filtered_classes)

    # fit k-means to determine the best cluster centers
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto", max_iter=300).fit(points_ogl / [n_clusters, 1, 1, 1, 1])
    cxywh = kmeans.cluster_centers_ * [n_clusters, 1, 1, 1, 1]

    plt.plot(points_prd[:, 1], points_prd[:, 2], ".")
    # plt.plot(points_ogl[:, 1], points_ogl[:, 2], ".")
    plt.plot(cxywh[:, 1], cxywh[:, 2], "+")
    plt.title(path_to_reference.stem)
    plt.show()

    # enforce positive integers as class ids
    class_ids = cxywh[:, 0].round().astype(int)

    # 1st: classify points
    cls = kmeans.predict(points_prd)
    # 2nd: determine variance
    xywh_min, xywh_max = [], []
    xywh_inner, xywh_outer = [], []
    for i in range(n_clusters):
        lg = cls == i
        c = class_ids[i]
        xy0 = cxywh[i, 1:3]
        wh = cxywh[i, 3:]

        fct = factor_std if isinstance(factor_std, (float, int)) else factor_std[c]

        xywh = points_prd[lg, 1:]
        diff_prd = xywh - cxywh[i, 1:]
        # # standard deviation
        wh_std = np.std(diff_prd[:, 2:], axis=0)
        dwh = fct * wh_std
        dwh = (max((dwh[0], 0.02)), max((dwh[1], 0.02)))
        wh_min = wh - dwh #+ diff_prd[:, 2:].min(axis=0)
        wh_max = wh + dwh #+ diff_prd[:, 2:].max(axis=0)

        xywh_min_i = np.hstack((xy0, wh_min)).clip(0, 1)
        xywh_max_i = np.hstack((xy0, wh_max)).clip(0, 1)

        # absolute min / max coordinates for inner / outer bboxes
        xyxy = xywh2xyxy(xywh)

        xy1_outer, xy2_inner = np.split(xyxy.min(axis=0), 2)
        xy1_inner, xy2_outer = np.split(xyxy.max(axis=0), 2)
        xyxy_inner = np.hstack((xy1_inner, xy2_inner))
        xyxy_outer = np.hstack((xy1_outer, xy2_outer))

        xywh_min_i = np.array((xywh.min(axis=0), xywh_min_i)).min(axis=0)
        xywh_max_i = np.array((xywh.max(axis=0), xywh_max_i)).max(axis=0)

        # combine
        xyxy_min = xywh2xyxy(xywh_min_i)
        xyxy_max = xywh2xyxy(xywh_max_i)
        xyxy_inner = np.hstack((np.max((xyxy_min[:2], xyxy_inner[:2]), axis=0), np.min((xyxy_min[2:], xyxy_inner[2:]), axis=0)))
        xyxy_outer = np.hstack((np.min((xyxy_max[:2], xyxy_outer[:2]), axis=0), np.max((xyxy_max[2:], xyxy_outer[2:]), axis=0)))

        assert (xyxy[:, :2] <= xyxy_inner[:2]).all() and (xyxy[:, 2:] >= xyxy_inner[2:]).all()
        assert (xyxy[:, :2] >= xyxy_outer[:2]).all() and (xyxy[:, 2:] <= xyxy_outer[2:]).all()

        xywh_inner = xyxy2xywh(xyxy_inner)
        xywh_outer = xyxy2xywh(xyxy_outer)
        xywh_min.append(xywh_inner)  # may not be negative!
        xywh_max.append(xywh_outer)

        # n_passed = sum((np.abs(diff) <= tol).all(axis=1))
        # print(f"Class-ID {i}: {n_passed} / {sum(lg)} (all: {n_passed == sum(lg)})")

    # to matrix
    xywh_min = np.vstack(xywh_min).clip(0, 1)
    xywh_max = np.vstack(xywh_max).clip(0, 1)

    # visualize
    if path_to_images:
        files = [Path(ln) for ln in read_file(path_to_reference)]
        for fl in files:
            # construct path to image
            stem = Path(fl).stem
            # find all images
            images = [el for el in path_to_images.glob(f"{stem}.*") if el.suffix.lower() in [".jpg", ".png", ".bmp", ".tiff"]]
            if len(images) > 0:
                img = Image.open(images[0]).convert("RGB")
                draw = ImageDraw.Draw(img)

                for box_xywh in np.vstack((xywh_min, xywh_max)):
                    box_xyxy = (np.hstack((box_xywh[:2] - box_xywh[2:] / 2, box_xywh[:2] + box_xywh[2:] / 2)) * (img.size * 2))
                    plot_one_box(box_xyxy.round().astype(int).tolist(), draw, color=(255, 0, 0))

                img.show()
                # stop loop
                break

    return class_ids, xywh_min, xywh_max


if __name__ == "__main__":
    filename_predictions = "CRU_TrnVal4pattern_L*.txt"
    filename_reference = "CRU_TrnVal4pattern_OGL_L*.txt"
    path_to_files = Path()
    path_to_image_folder= Path(r"C:\Users\schwmax\Proj\Coding\YOLOv7_scw\dataset\CRURotorAssembly\data_crop")

    filename_export = "desired_coordinates.yml"

    # classes !
    # {"Magnet": 0, "Empty": 1, "Circle Element CCW": 2, "Circle Element CW": 3} # filter classes!

    info = dict()
    for fl_ogl, fl_prd in zip(path_to_files.glob(filename_reference), path_to_files.glob(filename_predictions)):
        cls, bbox_min, bbox_max = determine_desired_coordinates(
            fl_prd,
            fl_ogl,
            {0: 20, 2: 25, 3: 25},
            path_to_image_folder,
            [0, 2, 3]
        )
        # store data
        info[fl_ogl.stem] = [
            {"class_id": c, "inner": xywh2xyxy(p_min).round(3).tolist(), "outer": xywh2xyxy(p_max).round(3).tolist()}
            for c, p_min, p_max in zip(cls.tolist(), bbox_min, bbox_max)
        ]

        # TODO visualize cluster positions!

    with open(path_to_files / filename_export, "w") as fid:
        yaml.dump(info, fid)




