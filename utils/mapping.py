from pathlib import Path
import yaml
import csv
from ast import literal_eval
import logging

from typing import Union, List, Dict, Tuple, Any


def read_mappings_from_csv(file: Union[str, Path], delimiter: str = ",") -> Tuple[Dict[int, str], Dict[int, str]]:
    class_map, color_map = dict(), dict()

    if isinstance(file, (str, Path)):
        file = Path(file)
        if file.is_file() and (file.suffix.lower() == ".csv"):
            with open(file, newline="") as fid:
                lines = list(csv.reader(fid, delimiter=delimiter))

            class_map = {int(el[0]): el[1] for el in lines}
            color_map = {int(el[0]): el[2] for el in lines if len(el) > 1}
    return class_map, color_map


def look_for_file(filename: Union[str, Path], folders: List[Path]) -> Path:
    path = Path()
    for p2fl in [filename] + [Path(el) / filename for el in folders]:
        if Path(p2fl).is_file():
            path = Path(p2fl)
            break
    return path


def get_dict_from_file_or_envs(config: Dict[str, Any], key: str):
    folder_head = Path(config["MODEL_FOLDER_HEAD"])
    folder_data = Path(config["MODEL_FOLDER_DATA"])

    mapping = config[key]

    if mapping is None or mapping == "":
        map_ = None
    elif Path(mapping).suffix in (".yaml", ".yml"):
        # if is YAML file:
        # identify path to file
        path_to_map = look_for_file(mapping, [folder_head, folder_data])
        logging.info(f"configuration: {key}. YAML file {path_to_map}.")
        # read file
        if path_to_map.is_file():
            with open(path_to_map, "r") as fid:
                map_ = yaml.safe_load(fid)
        else:
            map_ = None
    elif Path(mapping).suffix in (".txt", ".conf"):
        # if is text file:
        # identify path to file
        path_to_map = look_for_file(mapping, [folder_head, folder_data])
        logging.info(f"configuration: {key}. Text file {path_to_map}.")
        # read file
        if path_to_map.is_file():
            with open(path_to_map, "r") as fid:
                lines = fid.readlines()
            map_ = {i: ln.strip() for i, ln in enumerate(lines) if len(ln) > 3}
        else:
            map_ = None
    else:
        # else is string
        map_ = literal_eval(mapping)
        if isinstance(map_, list):
            # construct dictionary
            map_ = {i: el for i, el in enumerate(map_)}
    return map_

