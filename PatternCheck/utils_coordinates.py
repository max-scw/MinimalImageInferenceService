import yaml
from pathlib import Path
import logging

from typing import List, Dict, Tuple, Union


def load_yaml(path: Union[str, Path]) -> dict:
    if Path(path).is_file():
        with open(path, "rb") as fid:
            return yaml.safe_load(fid)
    else:
        raise FileNotFoundError()


def load_patterns(folder: Union[str, Path]) -> dict:
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Expecting a directory at {folder.as_posix()} but was none.")

    # find all YAML files
    extensions = [".yaml", ".yml"]
    files = [p for p in folder.rglob("*") if p.suffix in extensions]

    patterns = dict()
    for fl in files:
        patterns[fl.stem] = load_yaml(fl)
    logging.debug(f"{len(patterns)} Pattern(s) loaded from folder {folder.as_posix()}: {patterns}")
    return patterns


def is_xyxy(bboxes: List[List[float]]) -> bool:
    scale_to_xywh = False
    for bbx in bboxes:
        if (bbx[0] < bbx[2]) or (bbx[1] < bbx[3]):
            scale_to_xywh = True
            break
    return scale_to_xywh


def check_boxes(
        bboxes: List[List[Union[int, float]]],
        class_ids: List[int],
        config: Dict[str, Dict[str, Union[List[float], List[List[float]]]]],
) -> Tuple[str, List[bool]]:

    # check if boxes need to be scaled to center coordinates
    if is_xyxy(bboxes):
        bboxes = xyxy2xywh(bboxes)

    # loop through config to find box pattern
    info = ""
    found_boxes_best = []
    if config:
        for ky, vl in config.items():
            tol = vl["tolerance"]
            # reset found_boxes
            found_boxes = []
            for pos in vl["positions"]:
                id_des = pos[0]
                bbx_des = pos[1:5]

                # loop through actual boxes
                found = False
                for bbx_act, id_act in zip(bboxes, class_ids):
                    found = check_box(id_act, bbx_act, id_des, bbx_des, tol)
                    # shortcut
                    if found:
                        break
                found_boxes.append(found)

            if sum(found_boxes) > sum(found_boxes_best):
                info = ky
                found_boxes_best = found_boxes
                if all(found_boxes_best):
                    break

    return info, found_boxes_best


def check_box(id_act, bbx_act, id_des, bbx_des, tol) -> bool:
    found = False
    if id_act == id_des:
        # check difference
        for x1, x2, dx in zip(bbx_act, bbx_des, tol):
            if abs(x1 - x2) < dx:
                found = True
            else:
                found = False
                break
    return found




def xyxy2xywh(xyxy: List[List[float]]):
    """
    Convert to center coordinates [x_center, y_center, width, height]
    :param xyxy:
    :return:
    """
    # Convert nx4 boxes from [x1, y1, x2, y2] to [x, y, w, h] where xy1=top-left, xy2=bottom-right
    x0y0wh = []
    for x1, y1, x2, y2 in xyxy:
        # to center coordinates
        w = x2 - x1
        h = y2 - y1
        x0 = x1 + w / 2
        y0 = y1 + h / 2
        x0y0wh.append([x0, y0, w, h])
    return x0y0wh
