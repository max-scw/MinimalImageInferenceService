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


def determine_desired_coordinates(path_to_file: Path, factor_std: float = 2) -> Tuple[np.ndarray, np.ndarray]:
    # read file
    files = [Path(ln) for ln in read_file(path_to_file)]

    # cast to numeric
    labels = [read_label(fl) for fl in files]
    n_clusters = max([len(el) for el in labels])

    # flatten to get a list of data points
    points = np.vstack(labels)

    # merge classes
    lg = points[:, 0] == 1
    points[lg, 0] = 0

    # fit k-means to determine the best cluster centers
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init="auto").fit(points[:, 1:])
    xywh = kmeans.cluster_centers_

    # 1st: classify points
    cls = kmeans.predict(points[:, 1:])
    # 2nd: determine variance
    xywh_std = []
    for i in range(n_clusters):
        lg = cls == i
        std = np.std(points[lg, 1:] - xywh[i, :], axis=0)
        xywh_std.append(std)
    # to matrix
    xywh_std = np.vstack(xywh_std)

    xywh_tolerances = factor_std * xywh_std.max(axis=0)

    return xywh, xywh_tolerances


if __name__ == "__main__":
    filename = "Pattern_State_*.txt"
    path_to_files = Path()

    filename_export = "desired_coordinates.yml"

    info = dict()
    for fl in path_to_files.glob(filename):
        coordinates, tolerances = determine_desired_coordinates(fl, 2)
        info[fl.stem] = {"positions": coordinates.round(3).tolist(), "tolerance": tolerances.round(3).tolist()}

    with open(path_to_files / filename_export, "w") as fid:
        yaml.dump(info, fid)




