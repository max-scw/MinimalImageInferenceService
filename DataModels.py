from pydantic import BaseModel, Field

from pathlib import Path

from typing_extensions import Annotated
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
class CameraParameter(BaseModel):
    serial_number: Optional[int] = None
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None

    transmission_type: Optional[str] = None
    destination_ip_address: Optional[str] = None
    destination_port: Optional[Annotated[int, Field(strict=True, le=65535, ge=0)]] = None


class CameraPhotoParameter(CameraParameter):
    exposure_time_microseconds: Optional[int] = 10000
    timeout: Optional[int] = None  # milli seconds

    emulate_camera: bool = False
    # image
    format: Optional[str] = "jpeg"
    quality: Optional[Annotated[int, Field(strict=False,  le=100)]] = 85



class CameraInfo(CameraPhotoParameter):
    url: Union[str, Path]


# ----- Main
class ResultInference(BaseModel):
    bboxes: List[
        Tuple[
            Union[int, float],
            Union[int, float],
            Union[int, float],
            Union[int, float]
        ]
    ]
    class_ids: List[int]
    scores: List[float]


class OptionsReturnValuesMain(BaseModel):
    decision: Optional[bool] = True
    pattern_name: Optional[bool] = True
    img: Optional[bool] = True
    img_drawn: Optional[bool] = True
    # details
    bboxes: Optional[bool] = False
    class_ids: Optional[bool] = False
    scores: Optional[bool] = False


# class ResultMain(ResultInference):
#     decision: bool
#     pattern_name: Optional[str] = None
#     # images
#     image_original: Optional[str] = None # Base64 encoded
#     image_drawn: Optional[str] = None # Base64 encoded


# ----- Pattern-Check
class Pattern(BaseModel):
    positions: List[Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]]
    tolerances: List[Union[int, float]]


class PatternRequest(BaseModel):
    # bounding boxes: coordinates and classes
    coordinates: List[Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]]
    class_ids: List[int]
    # pattern to check against
    pattern_key: Optional[str] = None
    pattern: Optional[Union[Pattern, Dict[str, Pattern]]] = None


