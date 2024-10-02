import logging
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime

from typing import Union, Tuple, Literal


def bytes_to_image_array(image_bytes: object) -> np.ndarray:
    # Convert the bytes data to a numpy array
    np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
    # Decode the image using OpenCV
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    # convert color from OpenCV BGR format to RGB format
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def load_image(path_to_image: Union[str, Path], imgsz: Tuple[int, int]) -> np.ndarray:
    # ensure pathlib object
    path_to_image = Path(path_to_image)
    # read image
    img = cv2.imread(path_to_image.as_posix(), cv2.IMREAD_COLOR)
    # convert color from openCV-native BGR format to standard RGB format
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # resize image to desired size
    return resize_image(img, imgsz)


def resize_image(image: np.ndarray, imgsz: Tuple[int, int]) -> np.ndarray:
    imgsz_ogl = image.shape
    # interpolation method
    if imgsz_ogl[0] > imgsz[0] or imgsz_ogl[1] > imgsz[1]:  # shrinking image
        method = cv2.INTER_AREA
    else:  # stretching image
        method = cv2.INTER_CUBIC

    return cv2.resize(image, imgsz, interpolation=method)  # shrinking image


def adjust_image_channels(image: np.ndarray) -> np.ndarray:
    # img = letterbox(img0, self.img_size, stride=self.stride)[0] TODO
    # move color channels to front
    image = np.moveaxis(image, -1, 0)
    # add batch size
    image = np.expand_dims(image, 0)
    return image


def letterbox(
        img: np.ndarray,
        new_shape: Tuple[int, int] = (640, 640),
        color: Tuple[int, int, int] = (114, 114, 114),
        auto: bool = True,
        scale_fill: bool = False,
        scale_up: bool = True,
        stride: int = 32
):
    # Resize and pad image while meeting stride-multiple constraints
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    ratio = (new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scale_up:  # only scale down, do not scale up (for better test mAP)
        ratio = (min(el, 1.0) for el in ratio)

    # Compute padding
    new_unpad = (int(round(shape[1] * ratio[1])), int(round(shape[0] * ratio[0])))
    dw = new_shape[1] - new_unpad[0]  # width padding
    dh = new_shape[0] - new_unpad[1]  # height padding

    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scale_fill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = (new_shape[1] / shape[1], new_shape[0] / shape[0])  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, ratio, (dw, dh)


def prepare_image(
        image: np.ndarray,
        shape: Tuple[int, int],
        precision: Literal["fp64", "fp32", "fp16", "int8"] = None
) -> np.ndarray:
    msg = f"prepare_image({image.shape}, {shape}, {precision})"
    logging.debug(msg)

    # resize
    img_sml = letterbox(image, new_shape=shape, stride=32)[0]
    # move channels
    img_mdl = np.moveaxis(img_sml, (2, 0, 1), (0, 1, 2))
    # img_mdl = img_sml.transpose(2, 0, 1)  # bring color channels to front # BGR2RGB
    # normalize image (and convert to float)
    img_nrm = img_mdl / 255.0
    # add batch axis
    img_btc = img_nrm[np.newaxis, ...]
    # convert image
    img_out = img_btc.astype(precision_to_type(precision)) if precision is not None else img_btc
    logging.debug(f"prepare_image(): img_out.shape={img_out.shape}, img_out.dtype={img_out.dtype}")
    return img_out


def precision_to_type(precision: Literal["fp64", "fp32", "fp16", "int8"]) -> type:
    if precision.lower() == "fp64":
        return np.float64
    elif precision.lower() == "fp32":
        return np.float32
    elif precision.lower() == "fp16":
        return np.float16
    elif precision.lower() == "int8":
        return np.int8
    else:
        raise ValueError(f"Unknown precision: {precision}")


def save_image(image: np.ndarray, export_path: Path, marker: str = None) -> Path:
    # create "unique" filename
    filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    if marker:
        filename += f"_{marker}"
    # add suffix
    filename += ".webp"

    # write image to path
    path_to_file = export_path / filename
    if not path_to_file.exists():
        cv2.imwrite(path_to_file.as_posix(), image)
    # return file path
    return path_to_file


def scale_coordinates_to_image_size(
        bboxs: np.ndarray,
        size_src: Tuple[int, int],
        size_des: Tuple[int, int]
) -> np.ndarray:
    """
    Scale coordinates of bounding boxes to the size of the original image.

    Parameters:
        bboxs (np.ndarray): Array of bounding box coordinates in format [[x0, y0, x1, y1], ...].
        size_src (Tuple[int, int]): Size of the source image (width, height).
        size_des (Tuple[int, int]): Size of the destination image (width, height).

    Returns:
        np.ndarray: Array of scaled bounding box coordinates.
    """
    height_src, width_src = size_src
    height_des, width_des = size_des

    # Calculate scaling factors
    scale_x = width_des / width_src
    scale_y = height_des / height_src

    # Scale bounding box coordinates
    scaled_bboxs = np.zeros_like(bboxs, dtype=np.float32)
    scaled_bboxs[:, 0] = bboxs[:, 0] * scale_x
    scaled_bboxs[:, 1] = bboxs[:, 1] * scale_y
    scaled_bboxs[:, 2] = bboxs[:, 2] * scale_x
    scaled_bboxs[:, 3] = bboxs[:, 3] * scale_y

    return scaled_bboxs


if __name__ == "__main__":
    img = cv2.imread("../../BaslerCameraAdapter/test_images/20240813_120110.jpg")

    letterbox(img, new_shape=(544, 640))