import os
import sys
import argparse
import uuid
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.photogrammetry.job import PhotogrammetryJob
from pipeline.photogrammetry.odm_engine import ODMPhotogrammetryEngine
from pipeline.preprocessing.loader import load_point_cloud
from pipeline.preprocessing.filters import voxel_downsample, remove_statistical_outliers
from pipeline.preprocessing.stats import calculate_statistics
from pipeline.utils.logger import get_logger

logger = get_logger("RunPhotogrammetryCLI")

def main():
    parser = argparse.ArgumentParser(description="Run Photogrammetry Pipeline")
    parser.add_argument("--images", required=True, help="Path to input images directory")
    parser.add_argument("--output", default="data/outputs/photogrammetry", help="Output directory")
    parser.add_argument("--fast", action="store_true", help="Run ODM in fast orthophoto mode")
    parser.add_argument("--voxel-size", type=float, default=0.1, help="Voxel downsampling size")
    parser.add_argument("--outlier-neighbors", type=int, default=20, help="Statistical outlier neighbors")
    parser.add_argument("--outlier-ratio", type=float, default=2.0, help="Statistical outlier ratio")
    parser.add_argument("--resize", type=int, default=1024, help="Resize images to this dimension to save memory")
    
    args = parser.parse_args()
    
    engine = ODMPhotogrammetryEngine()
    
    if not engine.validate_environment():
        logger.error("Environment validation failed. Is Docker installed?")
        sys.exit(1)
        
    job_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(args.output, f"job_{job_id}")
    
    config = {}
    if args.fast:
        config["fast_orthophoto"] = True
        
    # Optimize quality for a detailed 3D model
    config["feature_quality"] = "high"
    config["pc_quality"] = "high"
        
    job = PhotogrammetryJob(
        job_id=job_id,
        image_directory=args.images,
        output_directory=output_dir,
        configuration=config
    )
    
    logger.info(f"Starting Photogrammetry Job {job_id}")
    job = engine.run(job)
    
    if job.status != "SUCCESS":
        logger.error(f"Job failed: {job.error_info}")
        sys.exit(1)
        
    # Output Validation & Processing
    try:
        logger.info("Validating and Processing Output Point Cloud...")
        
        # Load and validate
        pcd, meta = load_point_cloud(job.generated_point_cloud_path)
        
        # Validate no NaN/Inf (Open3D handles this somewhat, but we can check bounds)
        import numpy as np
        pts = np.asarray(pcd.points)
        if np.any(np.isnan(pts)) or np.any(np.isinf(pts)):
            raise ValueError("Point cloud contains NaN or Inf coordinates.")
            
        logger.info(f"Loaded generated point cloud with {meta['num_points']} points.")
        
        # Process (reusing M0 modules)
        downsampled, ds_info = voxel_downsample(pcd, voxel_size=args.voxel_size)
        filtered, filter_info = remove_statistical_outliers(downsampled, nb_neighbors=args.outlier_neighbors, std_ratio=args.outlier_ratio)
        
        # Stats
        stats = calculate_statistics(filtered)
        
        # Save processed
        processed_path = os.path.join(output_dir, "processed_cloud.ply")
        import open3d as o3d
        o3d.io.write_point_cloud(processed_path, filtered)
        
        # Generate report
        report = {
            "job_id": job.job_id,
            "status": job.status,
            "crs_info": job.crs_info or "NOT GEOREFERENCED",
            "execution_time_seconds": job.metrics.get("execution_time_seconds", 0),
            "original_points": meta['num_points'],
            "processed_points": stats['point_count'],
            "processing_steps": [ds_info, filter_info],
            "final_bounding_box": stats['dimensions'],
            "processed_cloud_path": processed_path
        }
        
        report_path = os.path.join(output_dir, "report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
            
        logger.info(f"Processing complete. Report saved to {report_path}")
        logger.info(f"Processed point cloud saved to {processed_path}")
        logger.info(f"Visualize with: python -c \"import open3d as o3d; o3d.visualization.draw_geometries([o3d.io.read_point_cloud('{processed_path.replace(chr(92), '/')}')])\"")
        
    except Exception as e:
        logger.error(f"Output validation/processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
