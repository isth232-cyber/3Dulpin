import os
import json
import numpy as np
import open3d as o3d
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.utils.logger import get_logger, log_operation

logger = get_logger("TestGenerator")

@log_operation(logger, "Generate Synthetic Building")
def generate_synthetic_building(output_path, num_floors=3, floor_height=3.0, width=15.0, depth=20.0, points_per_sqm=100, seed=42):
    """
    Generates a synthetic deterministic building point cloud.
    Includes ground, walls, floors, and a roof.
    """
    np.random.seed(seed)
    points_list = []
    
    # Helper to generate random points on a plane
    def generate_plane(min_bound, max_bound, density):
        area = (max_bound[0] - min_bound[0]) * (max_bound[1] - min_bound[1])
        if area == 0:
            area = (max_bound[0] - min_bound[0]) * (max_bound[2] - min_bound[2])
        if area == 0:
            area = (max_bound[1] - min_bound[1]) * (max_bound[2] - min_bound[2])
            
        n_points = int(area * density)
        pts = np.random.uniform(low=min_bound, high=max_bound, size=(n_points, 3))
        return pts

    # Ground plane (slightly larger than building)
    ground_min = np.array([-5.0, -5.0, 0.0])
    ground_max = np.array([width + 5.0, depth + 5.0, 0.0])
    points_list.append(generate_plane(ground_min, ground_max, points_per_sqm * 0.5))
    
    # Floors and Roof
    for f in range(num_floors + 1):
        z = f * floor_height
        f_min = np.array([0.0, 0.0, z])
        f_max = np.array([width, depth, z])
        points_list.append(generate_plane(f_min, f_max, points_per_sqm))
        
    # Walls (4 walls)
    total_height = num_floors * floor_height
    # Front wall (y=0)
    points_list.append(generate_plane(np.array([0.0, 0.0, 0.0]), np.array([width, 0.0, total_height]), points_per_sqm))
    # Back wall (y=depth)
    points_list.append(generate_plane(np.array([0.0, depth, 0.0]), np.array([width, depth, total_height]), points_per_sqm))
    # Left wall (x=0)
    points_list.append(generate_plane(np.array([0.0, 0.0, 0.0]), np.array([0.0, depth, total_height]), points_per_sqm))
    # Right wall (x=width)
    points_list.append(generate_plane(np.array([width, 0.0, 0.0]), np.array([width, depth, total_height]), points_per_sqm))

    all_points = np.vstack(points_list)
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(all_points)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    o3d.io.write_point_cloud(output_path, pcd)
    
    # Generate metadata
    metadata = {
        "num_points": len(all_points),
        "building_dimensions": {
            "width": width,
            "depth": depth,
            "height": total_height
        },
        "overall_bounding_box": {
            "min": np.min(all_points, axis=0).tolist(),
            "max": np.max(all_points, axis=0).tolist(),
            "width": float(np.max(all_points[:, 0]) - np.min(all_points[:, 0])),
            "depth": float(np.max(all_points[:, 1]) - np.min(all_points[:, 1])),
            "height": float(np.max(all_points[:, 2]) - np.min(all_points[:, 2]))
        },
        "floors": num_floors,
        "floor_height": floor_height,
        "description": "SYNTHETIC TEST DATA - Not real LiDAR/drone data. Includes ground plane extending beyond building.",
        "seed": seed
    }
    
    metadata_path = output_path.replace(".ply", "_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    logger.info(f"Saved synthetic point cloud to {output_path} ({len(all_points)} points)")
    return metadata

if __name__ == "__main__":
    output_file = os.path.join("data", "synthetic", "building.ply")
    generate_synthetic_building(output_file)
