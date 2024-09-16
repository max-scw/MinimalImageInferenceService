from PIL import Image, ImageDraw
import numpy as np

from matplotlib import pyplot as plt

from typing import List


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