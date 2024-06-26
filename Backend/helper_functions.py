import numpy as np
from PIL import Image
import io
import base64


def bytes_to_image(raw_image: bytes) -> Image:
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
