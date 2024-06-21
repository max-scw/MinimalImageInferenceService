from pathlib import Path
from PIL import Image
import numpy as np
from datetime import datetime
import io
import base64

from typing import Tuple


def save_image(
        image: Image,
        export_path: Path,
        marker: str = None,
        file_extension: str = ".webp"
) -> Path:
    # create "unique" filename
    filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    if marker:
        filename += f"_{marker}"
    # add suffix
    suffix = file_extension if file_extension[0] == "." else f".{file_extension}"
    filename = Path(filename).with_suffix(suffix)

    # write image to path
    path_to_file = export_path / filename
    if not path_to_file.exists():
        image.save(path_to_file)
    # return file path
    return path_to_file


def bytes_to_image(raw_image: bytes) -> Image:
    img_ary = np.frombuffer(raw_image, np.uint8)
    return Image.open(io.BytesIO(img_ary))


def resize_image(image: Image, size: Tuple[int, int] = None) -> Image:
    if isinstance(size, (tuple, list)):
        # PIL expect the size in the reverse order compared to torch
        size = size[::-1]

    image_ = image.copy()
    # see https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters-comparison-table for method comparison
    if size is not None:
        return image_.resize(size, Image.BICUBIC)
    else:
        return image_


def base64_to_image(string: str) -> Image:
    msg = base64.b64decode(string)
    buf = io.BytesIO(msg)
    return Image.open(buf)
