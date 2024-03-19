from pathlib import Path
from PIL import Image
import numpy as np
from datetime import datetime
import io


def save_image(
        image: np.ndarray,
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
        Image.fromarray(image).save(path_to_file)
    # return file path
    return path_to_file


def bytes_to_image(raw_image: bytes) -> Image:
    img_ary = np.frombuffer(raw_image, np.uint8)
    return Image.open(io.BytesIO(img_ary))