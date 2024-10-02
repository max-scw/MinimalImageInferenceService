from pathlib import Path
# from PIL import Image
import numpy as np

from tqdm import tqdm


def rotate_bounding_boxes_180_normalized(bboxes):
    """
    Rotate bounding boxes by 180 degrees for normalized coordinates.

    Parameters:
    - bboxes: list of bounding boxes in normalized xywh format [(x, y, w, h), ...]

    Returns:
    - list of transformed bounding boxes in normalized xywh format
    """
    rotated_bboxes = []

    for (x0, y0, w, h) in bboxes:
        # New top-left corner after 180-degree rotation
        x0_new = 1.0 - x0
        y0_new = 1.0 - y0

        # The width and height remain the same
        rotated_bboxes.append((x0_new, y0_new, w, h))

    return rotated_bboxes


if __name__ == '__main__':
    folder = Path(r"export")
    files = list(folder.glob("*.txt"))
    export_folder = Path("export_rotated")
    for fl in tqdm(files):

        labels = np.loadtxt(fl)
        bboxs = labels[:, 1:]

        bboxs_rot = rotate_bounding_boxes_180_normalized(bboxs)

        labels[:, 1:3] = np.array(bboxs_rot)[:, :2]
        export_folder.mkdir(exist_ok=True)
        with open(export_folder / fl.name, "w") as fid:
            fid.write("\n".join([" ".join([f"{el:.3g}" for el in row]) for row in labels]))
        # break
