from PIL import Image, ImageDraw, ImageFont, ImageColor
import numpy as np

from typing import Union, Tuple, List, Dict


def color2rgb(color: Union[Tuple[int, int, int], List[int], str, np.ndarray]) -> Tuple[int, int, int]:
    """
    converts hex color code or color tuple to RGB integer tuple.
    If no input is provided, a random color tuple is generated
    :param color:
    :return: RGB color tuple
    """
    if isinstance(color, str) and len(color) == 7 and color[0] == "#":
        # hex color code
        # color_ = ImageColor.getrgb(color)
        color_ = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    elif (isinstance(color, (tuple, list, np.ndarray)) and
          (len(color) == 3) and
          all([0 <= el <= 255 for el in color])):
        # RGB
        color_ = [int(el) for el in color]
    else:
        color_ = np.random.randint(0, 255, (3, ))
    return color_


def plot_one_box(
        box,
        draw: ImageDraw.ImageDraw,
        color: Union[Tuple[int, int, int], List[int], str] = None,
        label: str = None,
        line_thickness: int = 3,
        fontsize: int = 12
):
    color_ = color2rgb(color)

    draw.rectangle(box, width=line_thickness, outline=tuple(color_))  # plot
    if label:
        # font = ImageFont.truetype("arial.ttf", fontsize)
        font = ImageFont.load_default(fontsize)
        txt_width = font.getlength(label)
        txt_height = fontsize
        draw.rectangle([box[0], box[1] - txt_height + 4, box[0] + txt_width, box[1]], fill=tuple(color_))
        draw.text((box[0], box[1] - txt_height + 1), label, fill=(255, 255, 255), font=font)
    return True


def plot_bboxs(
        image: Union[np.ndarray, Image.Image],
        bbox: np.ndarray,
        scores: Union[List[float], np.ndarray],
        classes: Union[List[int], np.ndarray],
        line_thickness: int = None,
        class_map: Dict[int, str] = None,
        color_map: Dict[int, Union[str, Tuple[int, int, int], np.ndarray]] = None
) -> Image.Image:
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    # default line thickness is relative to the image size
    if line_thickness is None:
        line_thickness = int(min(image.size) / 150)
    # ensure minimal line thickness
    line_thickness = max(line_thickness, 3)

    # fontsize relative to image size
    fontsize = max(round(max(image.size) / 40), 12)

    # create draw object
    draw = ImageDraw.Draw(image)

    if color_map is None:
        color_map = dict()
    if class_map is None:
        class_map = dict()

    for xyxy, conf, cls in zip(bbox, scores, classes):
        cls = int(cls)  # ensure integer
        # text label
        label = f"{class_map[cls] if cls in class_map else cls} {conf:.2f}"
        # color
        if cls not in color_map:
            # random color if no color was provided
            color_map[cls] = np.random.randint(0, 255, (3, ))
        color = color_map[cls]

        plot_one_box(
            xyxy,
            draw,
            label=label,
            color=color,
            line_thickness=line_thickness,
            fontsize=fontsize
        )
    return image
