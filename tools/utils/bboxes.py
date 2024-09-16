import numpy as np

def xywh2xyxy(xywh: np.ndarray) -> np.ndarray:
    if not isinstance(xywh, np.ndarray):
        xywh = np.asarray(xywh)
    if len(xywh.shape) > 1:
        xy0 = xywh[:, :2]
        wh2 = xywh[:, 2:] / 2
    else:
        xy0 = xywh[:2]
        wh2 = xywh[2:] / 2

    return np.hstack((xy0 - wh2, xy0 + wh2))


def xyxy2xywh(xyxy: np.ndarray) -> np.ndarray:
    xy1, xy2 = np.split(xyxy, 2)
    wh = (xy2 - xy1)
    xy0 = xy1 + wh / 2

    return np.hstack((xy0, wh))