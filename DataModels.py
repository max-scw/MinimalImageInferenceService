from pydantic import BaseModel, Field
from enum import Flag, auto

from pathlib import Path


from DataModels_BaslerCameraAdapter import BaslerCameraSettings

from typing_extensions import Annotated
from typing import Optional, List, Dict, Tuple, Union, Literal

from utils import default_from_env
from DataModels_BaslerCameraAdapter import BaslerCameraSettings


# ----- Inference: NN-model
class InferenceInfo(BaseModel):
    url: Union[str, Path]
    class_map: Optional[Dict[int, str]] = None
    color_map: Optional[Dict[int, str]] = None,
    token: Optional[str] = None


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
    token: Union[str, None]


# ----- Main
class ReturnValuesMain(Flag):
    DECISION = auto()
    PATTERN_NAME = auto()
    IMAGE = auto()
    IMAGE_DRAWN = auto()
    # details
    BBOXES = auto()
    CLASS_IDS = auto()
    SCORES = auto()
    
    def __int__(self) -> int:
        return int(self.value)

class SettingsMain(BaseModel):
    pattern_key: Optional[str] = None
    min_score: Optional[Annotated[float, Field(strict=False, le=1, ge=0)]] = 0.5
    return_options: Optional[Annotated[int, Field(strict=False, le=int(~ReturnValuesMain(0)), ge=0)]] = int(~ReturnValuesMain(0))
    token: Optional[str] = None


# ----- Pattern-Check
class Pattern(BaseModel):
    class_id: int
    positions: Tuple[float, float, float, float]
    tolerances: Tuple[float, float, float, float]


class PatternRequest(BaseModel):
    # bounding boxes: coordinates and classes
    coordinates: List[Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]]
    class_ids: List[int]
    # pattern to check against
    pattern_key: Optional[str] = None
    pattern: Optional[Union[Pattern, Dict[str, Pattern]]] = None
