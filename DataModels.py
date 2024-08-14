from pydantic import BaseModel, Field

from pathlib import Path

from typing_extensions import Annotated
from typing import Optional, List, Dict, Tuple, Union, Literal

from utils import default_from_env
from DataModels_BaslerCameraAdapter import PhotoParams, BaslerCameraSettings


# ----- Inference: NN-model
class InferenceInfo(BaseModel):
    url: Union[str, Path]
    class_map: Optional[Dict[int, str]] = None
    color_map: Optional[Dict[int, str]] = None


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


# ----- Camera
class CameraInfo(BaslerCameraSettings):
    url: Union[str, Path]


# ----- Main
class SettingsMain(BaseModel):
    pattern_key: Optional[str] = None
    min_score: Optional[Annotated[float, Field(strict=False, le=1, ge=0)]] = 0.5


class OptionsReturnValuesMain(BaseModel):
    decision: Optional[bool] = True
    pattern_name: Optional[bool] = True
    img: Optional[bool] = True
    img_drawn: Optional[bool] = True
    # details
    bboxes: Optional[bool] = False
    class_ids: Optional[bool] = False
    scores: Optional[bool] = False


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


