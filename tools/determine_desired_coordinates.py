from pathlib import Path
import numpy as np
import yaml

from sklearn.cluster import KMeans

from typing import List, Tuple


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


def determine_desired_coordinates(path_to_file: Path, factor_std: float = 3):
    # read file
    files = [Path(ln) for ln in read_file(path_to_file)]

    # cast to numeric
    labels = [read_label(fl) for fl in files]
    n_clusters = max([len(el) for el in labels])
    print(f"Using {n_clusters} clusters.")

    # flatten to get a list of data points
    points = np.vstack(labels)

    # merge classes
    lg = points[:, 0] == 1
    points[lg, 0] = 0

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
        tol = factor_std * std

        n_passed = sum((np.abs(diff) <= tol).all(axis=1))
        print(f"Class-ID {i}: {n_passed} / {sum(lg)} (all: {n_passed == sum(lg)})")

        cxywh_tol.append(tol)
    # to matrix
    xywh_tolerances = np.vstack(cxywh_tol)

    # enforce positive integers as class ids
    cls = cxywh[:, 0].round().astype(int)
    return cls, cxywh[:, 1:], xywh_tolerances


if __name__ == "__main__":
    filename = "CRU_TrnVal4pattern_L*.txt"
    path_to_files = Path()

    filename_export = "desired_coordinates.yml"

    info = dict()
    for fl in path_to_files.glob(filename):
        cls, pos, tol = determine_desired_coordinates(fl, 6)
        info[fl.stem] = [
            {"class_id": c, "positions": p, "tolerance": t}
            for c, p, t in zip(cls.tolist(), pos.round(3).tolist(), tol.round(3).tolist())
        ]

        # TODO visualize cluster positions!

    with open(path_to_files / filename_export, "w") as fid:
        yaml.dump(info, fid)




