from pydantic import BaseModel

from typing import Optional, List, Tuple, Union, Dict


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
