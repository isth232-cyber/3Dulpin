from abc import ABC, abstractmethod
from pipeline.photogrammetry.job import PhotogrammetryJob

class PhotogrammetryEngine(ABC):
    @abstractmethod
    def validate_environment(self) -> bool:
        """Check if engine prerequisites are available."""
        pass

    @abstractmethod
    def run(self, job: PhotogrammetryJob) -> PhotogrammetryJob:
        """Execute the photogrammetry job."""
        pass
