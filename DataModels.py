from pydantic import BaseModel
from pathlib import Path

from typing import Optional, List, Dict, Tuple, Union, Literal



# class AppSettings(BaseModel):
#     data_folder: Path
#     impress: Optional[ImpressInfo] = None
#     title: Optional[str] = None
#     description: Optional[str] = None
#     file_type_save_image: Optional[str] = ".webp"
#     bbox_pattern: Optional[dict] = None
#     image_size: Optional[Tuple[int, int]] = None
#     min_score: Optional[float] = 0.5


# ----- Inference: NN-model
class InferenceInfo(BaseModel):
    url: Union[str, Path]
    class_map: Optional[Dict[int, str]] = None
    color_map: Optional[Dict[int, str]] = None


# ----- Camera
class CameraInfo(BaseModel):
    url: Union[str, Path]
    exposure_time_microseconds: Optional[int] = 10000

    serial_number: Optional[int] = None
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None

    timeout_ms: Optional[int] = None
    transmission_type: Optional[str] = None
    destination_ip_address: Optional[str] = None
    destination_port: Optional[int] = None

    image_extension: Optional[str] = None

    emulate_camera: bool = False


# ----- Pattern-Check
class Pattern(BaseModel):
    positions: List[List[Union[int, float]]]
    tolerances: List[Union[int, float]]


class PatternRequest(BaseModel):
    # bounding boxes: coordinates and classes
    coordinates: List[List[Union[int, float]]]
    class_ids: List[int]
    # pattern to check against
    pattern_key: Optional[str] = None
    pattern: Optional[Union[Pattern, Dict[str, Pattern]]] = None