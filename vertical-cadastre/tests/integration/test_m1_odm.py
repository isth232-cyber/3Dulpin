import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from pipeline.photogrammetry.odm_engine import ODMPhotogrammetryEngine
from pipeline.photogrammetry.job import PhotogrammetryJob

# Environment variable to trigger real integration tests
REAL_DATASET_PATH = os.environ.get("VERTICAL_CADASTRE_REAL_DRONE_DATA", None)

@pytest.mark.skipif(not REAL_DATASET_PATH, reason="PENDING REAL DATASET: No real drone dataset provided.")
def test_real_odm_integration_execution(tmp_path):
    """REAL ODM INTEGRATION TEST: Full ODM Execution"""
    engine = ODMPhotogrammetryEngine()
    
    # Must have Docker
    assert engine.validate_environment(), "Docker is not available for real integration test."
    
    output_dir = tmp_path / "odm_out"
    
    job = PhotogrammetryJob(
        job_id="int_test",
        image_directory=REAL_DATASET_PATH,
        output_directory=str(output_dir),
        configuration={"fast_orthophoto": True}
    )
    
    job = engine.run(job)
    
    assert job.status == "SUCCESS"
    assert job.generated_point_cloud_path is not None
    assert os.path.exists(job.generated_point_cloud_path)
    
    # Validate point cloud
    import open3d as o3d
    import numpy as np
    pcd = o3d.io.read_point_cloud(job.generated_point_cloud_path)
    assert not pcd.is_empty()
    pts = np.asarray(pcd.points)
    assert not np.any(np.isnan(pts))
    assert not np.any(np.isinf(pts))
