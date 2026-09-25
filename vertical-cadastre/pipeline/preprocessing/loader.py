import os
import open3d as o3d
import numpy as np
from typing import Tuple
from pipeline.utils.logger import get_logger

logger = get_logger("DataLoader")

def load_point_cloud(filepath: str) -> Tuple[o3d.geometry.PointCloud, dict]:
    """
    Loads a point cloud and reports basic properties.
    Validates file existence and handles errors.
    
    Returns:
        tuple: (PointCloud object, metadata dictionary)
    """
    if not os.path.exists(filepath):
        logger.error(f"Point cloud file not found: {filepath}")
        raise FileNotFoundError(f"Point cloud file not found: {filepath}")
        
    logger.info(f"Loading point cloud from {filepath}")
    pcd = o3d.io.read_point_cloud(filepath)
    
    if pcd.is_empty():
        logger.error(f"Loaded point cloud is empty or invalid format: {filepath}")
        raise ValueError(f"Loaded point cloud is empty or invalid format: {filepath}")
        
    pts = np.asarray(pcd.points)
    num_points = len(pts)
    min_bound = pcd.get_min_bound()
    max_bound = pcd.get_max_bound()
    
    metadata = {
        "filepath": filepath,
        "num_points": num_points,
        "min_bound": min_bound.tolist(),
        "max_bound": max_bound.tolist()
    }
    
    logger.info(f"Successfully loaded {num_points} points.")
    logger.info(f"Bounds: Min {min_bound}, Max {max_bound}")
    
    return pcd, metadata
