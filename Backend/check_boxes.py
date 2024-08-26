import yaml
from pathlib import Path
import logging
import warnings

from typing import List, Dict, Tuple, Union, Any


def get_patterns_from_config(config: Dict[str, Any]) -> Tuple[dict, str]:

    if "PATTERN_FILE" in config:
        file = config["PATTERN_FILE"]
    else:
        warnings.warn("No folder provided where patterns are stored in.")
        return dict(), ""

    # load patterns
    patterns = load_patterns(file)
    # get default pattern key
    default_pattern_key = config["PATTERN_DEFAULT"] if "PATTERN_DEFAULT" in config else None

    # use fist pattern if no pattern key was provided
    if not default_pattern_key:
        if len(patterns) > 0:
            default_pattern_key = list(patterns.keys())[0]
            logging.info(f"No default pattern key provided. Using '{default_pattern_key}' as default pattern")
        else:
            logging.warning(f"No pattern file found in {file}.")
    elif default_pattern_key not in patterns:
        msg = f"Default pattern '{default_pattern_key}' not found in {file}"
        logging.error(msg)
        raise Exception(msg)
    return patterns, default_pattern_key


def load_yaml(path: Union[str, Path]) -> dict:
    if Path(path).is_file():
        with open(path, "rb") as fid:
            return yaml.safe_load(fid)
    else:
        raise FileNotFoundError()


def load_patterns(path_to_pattern: Union[str, Path]) -> dict:
    path_to_pattern = Path(path_to_pattern)
    # expected file extensions
    extensions = [".yaml", ".yml"]

    if path_to_pattern.is_dir():
        # find all YAML files
        files = [p for p in path_to_pattern.rglob("*") if p.suffix in extensions]
    elif path_to_pattern.is_file() and (path_to_pattern.suffix in extensions):
        files = [path_to_pattern]
    else:
        raise FileNotFoundError(f"No YAML files found in {path_to_pattern}")

    patterns = dict()
    for fl in files:
        patterns[fl.stem] = load_yaml(fl)
    logging.debug(f"{len(patterns)} Pattern(s) loaded from {path_to_pattern.as_posix()}: {patterns}")

    return patterns


def is_xyxy(bboxes: List[List[float]]) -> bool:
    scale_to_xywh = False
    for bbx in bboxes:
        if (bbx[0] < bbx[2]) or (bbx[1] < bbx[3]):
            scale_to_xywh = True
            break
    return scale_to_xywh


def check_boxes(
        bboxes: List[Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]],
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
