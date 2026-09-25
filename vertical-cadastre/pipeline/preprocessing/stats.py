import open3d as o3d
import numpy as np

def calculate_statistics(pcd: o3d.geometry.PointCloud) -> dict:
    """
    Calculates detailed geometric statistics for a point cloud.
    
    Returns:
        dict: Structured statistics data
    """
    if pcd.is_empty():
        raise ValueError("Cannot calculate statistics for an empty point cloud.")
        
    pts = np.asarray(pcd.points)
    
    min_b = pcd.get_min_bound()
    max_b = pcd.get_max_bound()
    
    width = max_b[0] - min_b[0]
    depth = max_b[1] - min_b[1]
    height = max_b[2] - min_b[2]
    
    centroid = pcd.get_center()
    
    stats = {
        "point_count": len(pts),
        "min": {
            "x": min_b[0],
            "y": min_b[1],
            "z": min_b[2]
        },
        "max": {
            "x": max_b[0],
            "y": max_b[1],
            "z": max_b[2]
        },
        "dimensions": {
            "width": width,
            "depth": depth,
            "height": height
        },
        "centroid": centroid.tolist()
    }
    
    return stats
