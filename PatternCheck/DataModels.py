from pydantic import BaseModel

from typing import Optional, List, Tuple, Union


class PatternRequest(BaseModel):
    pattern_key: Optional[str] = None
    coordinates: List[List[Union[int, float]]]
    class_ids: List[int]
