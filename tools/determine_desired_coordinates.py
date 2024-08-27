from pathlib import Path
import numpy as np
import yaml

from sklearn.cluster import KMeans

from PIL import Image, ImageDraw
from matplotlib import pyplot as plt

from typing import List, Tuple, Union, Dict


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


def draw_rectangles(
        img: Image,
        xywh,
        xywh_tol,
        ids: List[int],
        thickness: int = 2,
        colormap: str = "tab10"
) -> Image:
    draw = ImageDraw.Draw(img)
    # bounding box
    xy = xywh[:, :2] * img.size
    xy_tol = xywh_tol[:, :2] * img.size
    centers = np.hstack((xy - xy_tol, xy + xy_tol))

    wh = xywh[:, 2:] * img.size
    wh_tol = xywh_tol[:, 2:] * img.size

    center_size = np.hstack((xy - wh / 2 - wh_tol, xy + wh / 2 + wh_tol))

    # get colormap
    cmap = plt.get_cmap(colormap)
    # Retrieve colors as a list of RGB tuples
    colors = [cmap(i) for i in range(cmap.N)]
    # convert to 255 scale
    colors = (np.array(colors) * 255).astype(int)

    for cid, color in zip(np.unique(ids), colors):
        lg = cid == ids
        for xyxy in centers[lg, :].round().astype(int).tolist():
            draw.rectangle(xyxy, width=thickness, outline=tuple(color))

        for xyxy in center_size[lg, :].round().astype(int).tolist():
            draw.rectangle(xyxy, width=thickness, outline=tuple(color))

    return img


def determine_desired_coordinates(
        path_to_file: Path,
        factor_std: Union[float, Dict[int, float]] = 3,
        path_to_images: Path = None,
        filtered_classes: List[int] = None
):
    # read file
    files = [Path(ln) for ln in read_file(path_to_file)]

    # cast to numeric
    labels = [read_label(fl) for fl in files]
    n_clusters = max([len(el) for el in labels])
    print(f"Using {n_clusters} clusters.")

    # flatten to get a list of data points
    points = np.vstack(labels)

    # filter classes
    if filtered_classes:
        lg = [el in filtered_classes for el in points[:, 0]]
        points = points[lg]

    # fit k-means to determine the best cluster centers
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init="auto").fit(points)
    cxywh = kmeans.cluster_centers_

    # 1st: classify points
    cls = kmeans.predict(points)
    # 2nd: determine variance
    cxywh_tol = []
    for i in range(n_clusters):
        lg = cls == i
        #
        diff = points[lg, 1:] - cxywh[i, 1:]
        # standard deviation
        std = np.std(diff, axis=0)
        # tolerance
        # class
        c = cxywh[i, 0].round().astype(int)
        fct = factor_std if isinstance(factor_std, (float, int)) else factor_std[c]
        tol = fct * std

        n_passed = sum((np.abs(diff) <= tol).all(axis=1))
        print(f"Class-ID {i}: {n_passed} / {sum(lg)} (all: {n_passed == sum(lg)})")

        cxywh_tol.append(tol)
    # to matrix
    xywh_tolerances = np.vstack(cxywh_tol)

    # enforce positive integers as class ids
    class_ids = cxywh[:, 0].round().astype(int)
    xywh = cxywh[:, 1:]

    # visualize
    if path_to_images:
        for fl in files:
            # construct path to image
            stem = Path(fl).stem
            # find all images
            images = [el for el in path_to_images.glob(f"{stem}.*") if el.suffix.lower() in [".jpg", ".png", ".bmp", ".tiff"]]
            if len(images) > 0:
                img = Image.open(images[0]).convert("RGB")

                img = draw_rectangles(
                    img,
                    xywh,
                    xywh_tolerances,
                    ids=class_ids,
                    thickness=5,
                    colormap="tab10"
                )
                img.show()
                # stop loop
                break

    return class_ids, xywh, xywh_tolerances


if __name__ == "__main__":
    filename = "CRU_TrnVal4pattern_L*.txt"
    path_to_files = Path()

    filename_export = "desired_coordinates.yml"

    # classes !
    # {"Magnet": 0, "Empty": 1, "Circle Element CCW": 2, "Circle Element CW": 3} # filter classes!

    info = dict()
    for fl in path_to_files.glob(filename):
        cls, pos, tol = determine_desired_coordinates(
            fl,
            {0: 20, 2: 30, 3: 30},
            Path(r"C:\Users\schwmax\Proj\Coding\YOLOv7_scw\dataset\CRURotorAssembly\data"),
            [0, 2, 3]
        )
        # store data
        info[fl.stem] = [
            {"class_id": c, "positions": p, "tolerance": t}
            for c, p, t in zip(cls.tolist(), pos.round(3).tolist(), tol.round(3).tolist())
        ]

        # TODO visualize cluster positions!

    with open(path_to_files / filename_export, "w") as fid:
        yaml.dump(info, fid)




