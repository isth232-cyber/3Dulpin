import open3d as o3d
import numpy as np
from pipeline.utils.logger import get_logger, log_operation

logger = get_logger("PreprocessingFilters")

@log_operation(logger, "Voxel Downsampling")
def voxel_downsample(pcd: o3d.geometry.PointCloud, voxel_size: float = 0.05) -> tuple:
    """
    Downsamples point cloud using a voxel grid.
    
    Returns:
        tuple: (downsampled_pcd, processing_info_dict)
    """
    in_points = len(pcd.points)
    
    downsampled = pcd.voxel_down_sample(voxel_size=voxel_size)
    out_points = len(downsampled.points)
    
    info = {
        "operation": "voxel_downsampling",
        "parameters": {"voxel_size": voxel_size},
        "input_points": in_points,
        "output_points": out_points,
        "reduction_ratio": 1.0 - (out_points / in_points) if in_points > 0 else 0
    }
    
    logger.info(f"Voxel downsampling (size={voxel_size}): {in_points} -> {out_points} points")
    return downsampled, info

@log_operation(logger, "Statistical Outlier Removal")
def remove_statistical_outliers(pcd: o3d.geometry.PointCloud, nb_neighbors: int = 20, std_ratio: float = 2.0) -> tuple:
    """
    Removes noise using statistical outlier removal.
    
    Returns:
        tuple: (filtered_pcd, processing_info_dict)
    """
    in_points = len(pcd.points)
    
    cl, ind = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
    filtered = pcd.select_by_index(ind)
    out_points = len(filtered.points)
    
    info = {
        "operation": "statistical_outlier_removal",
        "parameters": {"nb_neighbors": nb_neighbors, "std_ratio": std_ratio},
        "input_points": in_points,
        "output_points": out_points,
        "reduction_ratio": 1.0 - (out_points / in_points) if in_points > 0 else 0
    }
    
    logger.info(f"Outlier removal (nb_neighbors={nb_neighbors}, std_ratio={std_ratio}): {in_points} -> {out_points} points")
    return filtered, info
