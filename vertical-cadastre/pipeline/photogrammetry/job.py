from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime

@dataclass
class PhotogrammetryJob:
    job_id: str
    image_directory: str
    output_directory: str
    configuration: Dict[str, any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "INITIALIZED"  # INITIALIZED, RUNNING, SUCCESS, FAILED
    generated_point_cloud_path: Optional[str] = None
    crs_info: Optional[str] = None
    error_info: Optional[str] = None
    metrics: Dict[str, any] = field(default_factory=dict)
