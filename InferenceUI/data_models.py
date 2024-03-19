from pydantic import BaseModel
from pathlib import Path

from typing import Optional, List, Dict, Tuple, Union, Literal

from utils_streamlit import ImpressInfo


class AppSettings(BaseModel):
    data_folder: Path
    impress: Optional[ImpressInfo] = None
    title: Optional[str] = None
    description: Optional[str] = None


class ModelInfo(BaseModel):
    path: Union[str, Path]
    class_map: Optional[Dict[int, str]] = None
    color_map: Optional[Dict[int, str]] = None
    image_size: Optional[Tuple[int, int]] = None
    precision: Optional[Literal["fp32", "fp16", "int8"]] = "fp32"


class CameraInfo(BaseModel):
    url: Union[str, Path]
    exposure_time_microseconds: Optional[int] = 10000

    serial_number: Optional[int] = None
    ip_address: Optional[str] = None

    timeout_ms: Optional[int] = None
    transmission_type: Optional[str] = None
    destination_ip_address: Optional[str] = None
    destination_port: Optional[int] = None

    emulate_camera: bool = False
