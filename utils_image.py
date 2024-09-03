from pathlib import Path
from PIL import Image
from datetime import datetime
import numpy as np

import io
import base64

from typing import Union, List, Tuple


def bytes_to_image_pil(raw_image: bytes) -> Image:
    img_ary = np.frombuffer(raw_image, np.uint8)
    return Image.open(io.BytesIO(img_ary))


def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()


def base64_to_image(string: str) -> Image:
    msg = base64.b64decode(string)
    buf = io.BytesIO(msg)
    return Image.open(buf)


# ----- image manipulation
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


def save_image(
        img: Image,
        image_extension: str,
        folder: Union[str, Path] = None,
        note: Union[str, List[str]] = None
) -> Union[Path, None]:
    if note is None:
        notes = []
    elif isinstance(note, str):
        notes = [""] + [note]
    elif isinstance(note, list):
        notes = [""] + [f"{el}" for el in note]
    else:
        raise TypeError(f"Expecting input 'note' to be a string or a list of strings but was {type(note)}.")

    # create filename from current timestamp
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_".join(notes)
    # create full path (not necessarily absolute)
    folder = Path(folder)
    if not folder.is_dir():
        folder.mkdir(exist_ok=True)
    path_to_file = Path(folder) / filename

    # file extension
    extension = image_extension.strip('.').lower()
    if extension == "jpeg":
        extension = "jpg"

    # save image
    if not path_to_file.exists():
        img.save(path_to_file.with_suffix(f".{extension}"))
        return path_to_file
    else:
        return None
