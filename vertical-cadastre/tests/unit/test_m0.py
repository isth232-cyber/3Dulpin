import os
import sys
import pytest
import numpy as np
import open3d as o3d

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.generate_test_data import generate_synthetic_building
from pipeline.preprocessing.loader import load_point_cloud
from pipeline.preprocessing.filters import voxel_downsample, remove_statistical_outliers
from pipeline.preprocessing.stats import calculate_statistics

TEST_FILE = "data/synthetic/test_m0_building.ply"

@pytest.fixture(scope="module")
def setup_test_data():
    """Generates test data for the entire test module"""
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    
    metadata = generate_synthetic_building(
        TEST_FILE, 
        num_floors=2, 
        floor_height=3.0, 
        width=10.0, 
        depth=10.0, 
        points_per_sqm=50, 
        seed=42
    )
    yield metadata
    
    # Teardown
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    metadata_file = TEST_FILE.replace(".ply", "_metadata.json")
    if os.path.exists(metadata_file):
        os.remove(metadata_file)

def test_1_synthetic_dataset_generation(setup_test_data):
    """Req 1: Synthetic dataset generation"""
    metadata = setup_test_data
    assert os.path.exists(TEST_FILE), "PLY file was not created"
    
    # Verify metadata corresponds to actual file size
    assert metadata["num_points"] > 0, "Point cloud should not be empty"
    
    # Verify building vs bounds distinction
    assert metadata["building_dimensions"]["width"] == 10.0
    assert metadata["building_dimensions"]["depth"] == 10.0
    assert metadata["building_dimensions"]["height"] == 6.0
    
    # Ground plane is built as [-5, -5] to [width+5, depth+5] = 20x20
    assert metadata["overall_bounding_box"]["width"] == pytest.approx(20.0, rel=1e-2)
    assert metadata["overall_bounding_box"]["depth"] == pytest.approx(20.0, rel=1e-2)
    assert metadata["overall_bounding_box"]["height"] == pytest.approx(6.0, rel=1e-2)

def test_2_point_cloud_loading(setup_test_data):
    """Req 2: Point-cloud loading"""
    pcd, meta = load_point_cloud(TEST_FILE)
    assert isinstance(pcd, o3d.geometry.PointCloud), "Should return an Open3D PointCloud object"
    assert len(pcd.points) > 0, "Loaded point cloud should not be empty"

def test_3_point_count_calculation(setup_test_data):
    """Req 3: Point count calculation"""
    pcd, meta = load_point_cloud(TEST_FILE)
    stats = calculate_statistics(pcd)
    
    expected_points = setup_test_data["num_points"]
    assert stats["point_count"] == expected_points, "Point count in stats should match exactly"

def test_4_bounding_box_calculation(setup_test_data):
    """Req 4: Bounding-box calculation"""
    pcd, _ = load_point_cloud(TEST_FILE)
    stats = calculate_statistics(pcd)
    
    # Numerically verify the bounding box width matches the overall bounding box (20x20x6)
    assert stats["dimensions"]["width"] == pytest.approx(20.0, rel=1e-2)
    assert stats["dimensions"]["depth"] == pytest.approx(20.0, rel=1e-2)
    assert stats["dimensions"]["height"] == pytest.approx(6.0, rel=1e-2)
    
def test_5_voxel_downsampling(setup_test_data):
    """Req 5: Voxel downsampling"""
    pcd, _ = load_point_cloud(TEST_FILE)
    original_count = len(pcd.points)
    
    voxel_size = 1.0
    downsampled, info = voxel_downsample(pcd, voxel_size=voxel_size)
    
    # Verify exact numeric reduction
    assert len(downsampled.points) > 0, "Downsampled cloud should have points"
    assert len(downsampled.points) < original_count, "Downsampled cloud must be smaller than original"
    
    # Verify logged info matches reality
    assert info["input_points"] == original_count
    assert info["output_points"] == len(downsampled.points)
    
    expected_ratio = 1.0 - (len(downsampled.points) / original_count)
    assert info["reduction_ratio"] == pytest.approx(expected_ratio, rel=1e-5)

def test_6_statistical_outlier_removal(setup_test_data):
    """Req 6: Statistical outlier removal"""
    pcd, _ = load_point_cloud(TEST_FILE)
    
    # Add a distant outlier point
    pts = np.asarray(pcd.points)
    outlier = np.array([[1000.0, 1000.0, 1000.0]])
    noisy_pts = np.vstack((pts, outlier))
    
    noisy_pcd = o3d.geometry.PointCloud()
    noisy_pcd.points = o3d.utility.Vector3dVector(noisy_pts)
    original_count = len(noisy_pcd.points)
    
    filtered, info = remove_statistical_outliers(noisy_pcd, nb_neighbors=20, std_ratio=1.0)
    
    # Outlier should definitely be removed
    assert len(filtered.points) < original_count, "Outlier must be removed"
    assert info["output_points"] == len(filtered.points)
    
    # Verify bounding box no longer contains the distant outlier
    stats = calculate_statistics(filtered)
    assert stats["max"]["x"] < 500.0, "Distant outlier should not be in the bounding box"

def test_7_invalid_file_handling():
    """Req 7: Invalid file handling"""
    non_existent_file = "data/synthetic/this_file_does_not_exist_at_all.ply"
    
    with pytest.raises(FileNotFoundError) as exc_info:
        load_point_cloud(non_existent_file)
    
    assert "not found" in str(exc_info.value).lower()
    
    # Create an empty, invalid PLY
    invalid_file = "data/synthetic/invalid_test.ply"
    os.makedirs(os.path.dirname(invalid_file), exist_ok=True)
    with open(invalid_file, 'w') as f:
        f.write("This is not a PLY file")
        
    with pytest.raises(ValueError) as exc_info:
        load_point_cloud(invalid_file)
        
    assert "empty or invalid" in str(exc_info.value).lower()
    
    if os.path.exists(invalid_file):
        os.remove(invalid_file)

def test_8_deterministic_synthetic_data_generation():
    """Req 8: Deterministic synthetic-data generation"""
    test_file_a = "data/synthetic/deterministic_a.ply"
    test_file_b = "data/synthetic/deterministic_b.ply"
    
    # Generate A
    generate_synthetic_building(test_file_a, num_floors=2, floor_height=3.0, width=5.0, depth=5.0, points_per_sqm=50, seed=123)
    pcd_a, _ = load_point_cloud(test_file_a)
    pts_a = np.asarray(pcd_a.points)
    
    # Generate B with identical seed
    generate_synthetic_building(test_file_b, num_floors=2, floor_height=3.0, width=5.0, depth=5.0, points_per_sqm=50, seed=123)
    pcd_b, _ = load_point_cloud(test_file_b)
    pts_b = np.asarray(pcd_b.points)
    
    # Exact numeric equivalence
    assert pts_a.shape == pts_b.shape, "Point counts must match exactly"
    assert np.allclose(pts_a, pts_b), "Coordinates must match exactly"
    
    # Generate C with different seed
    test_file_c = "data/synthetic/deterministic_c.ply"
    generate_synthetic_building(test_file_c, num_floors=2, floor_height=3.0, width=5.0, depth=5.0, points_per_sqm=50, seed=999)
    pcd_c, _ = load_point_cloud(test_file_c)
    pts_c = np.asarray(pcd_c.points)
    
    # Should differ
    assert not np.allclose(pts_a, pts_c), "Different seeds must produce different point distributions"
    
    # Cleanup
    for f in [test_file_a, test_file_b, test_file_c]:
        if os.path.exists(f):
            os.remove(f)
        meta_f = f.replace(".ply", "_metadata.json")
        if os.path.exists(meta_f):
            os.remove(meta_f)
