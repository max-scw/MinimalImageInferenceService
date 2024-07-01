from pydantic import BaseModel
from pathlib import Path

from utils_streamlit import ImpressInfo

from typing import Optional, Tuple


class AppSettings(BaseModel):
    address_backend: str
    timeout: Optional[int] = 10000  # ms?
    data_folder: Path
    impress: Optional[ImpressInfo] = None
    title: Optional[str] = None
    description: Optional[str] = None
    # file_type_save_image: Optional[str] = ".jpg"
    # bbox_pattern: Optional[dict] = None
    image_size: Optional[Tuple[int, int]] = None
