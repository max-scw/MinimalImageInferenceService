from pydantic import BaseModel
from datetime import datetime

from typing import Optional, List, Dict


class ImpressInfo(BaseModel):
    project_name: str
    author: str
    status: str
    date_up_since: datetime
    additional_info: Optional[dict] = None,
    project_link: Optional[str] = None
