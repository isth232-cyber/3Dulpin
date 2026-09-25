import os
import subprocess
import time
from datetime import datetime
import shutil

from pipeline.photogrammetry.engine import PhotogrammetryEngine
from pipeline.photogrammetry.job import PhotogrammetryJob
from pipeline.photogrammetry.validation import validate_input_directory
from pipeline.utils.logger import get_logger

logger = get_logger("ODMPhotogrammetryEngine")

class ODMPhotogrammetryEngine(PhotogrammetryEngine):
    def validate_environment(self) -> bool:
        """Check if Docker is installed and accessible."""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Docker is available: {result.stdout.strip()}")
                return True
            else:
                logger.error("Docker command failed.")
                return False
        except FileNotFoundError:
            logger.error("Docker is not installed or not in PATH.")
            return False

    def run(self, job: PhotogrammetryJob) -> PhotogrammetryJob:
        """Execute ODM via Docker."""
        job.start_time = datetime.now()
        job.status = "RUNNING"
        
        # 1. Validate Input
        is_valid, msg, images = validate_input_directory(job.image_directory)
        if not is_valid:
            job.status = "FAILED"
            job.error_info = f"Input validation failed: {msg}"
            job.end_time = datetime.now()
            return job
            
        # 2. Workspace Setup
        dataset_dir = os.path.abspath(job.output_directory)
        images_dir = os.path.join(dataset_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Copy images to workspace (ODM requires them in 'images' folder)
        try:
            for img_path in images:
                shutil.copy2(img_path, images_dir)
        except Exception as e:
            job.status = "FAILED"
            job.error_info = f"Failed to prepare workspace: {str(e)}"
            job.end_time = datetime.now()
            return job

        # 3. Construct Docker Command
        # Use opendronemap/odm:gpu image
        docker_cmd = [
            "docker", "run", "--rm", "--gpus", "all",
            "-v", f"{dataset_dir}:/datasets/code",
            "opendronemap/odm:gpu",
            "--project-path", "/datasets",
            "--max-concurrency", "14"
        ]
        
        if job.configuration.get("fast_orthophoto", False):
            docker_cmd.append("--fast-orthophoto")
            
        if "feature_quality" in job.configuration:
            docker_cmd.extend(["--feature-quality", job.configuration["feature_quality"]])
            
        if "pc_quality" in job.configuration:
            docker_cmd.extend(["--pc-quality", job.configuration["pc_quality"]])
            
        logger.info(f"Running ODM with command: {' '.join(docker_cmd)}")
        
        # 4. Execute
        try:
            # We use subprocess.Popen to capture output real-time if needed, but run is simpler for now
            start_proc_time = time.time()
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            exec_time = time.time() - start_proc_time
            
            job.metrics["execution_time_seconds"] = exec_time
            job.metrics["exit_code"] = result.returncode
            
            # Save logs
            with open(os.path.join(dataset_dir, "odm_execution.log"), 'w') as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n--- STDERR ---\n")
                    f.write(result.stderr)
                    
            if result.returncode != 0:
                job.status = "FAILED"
                job.error_info = f"ODM exited with code {result.returncode}. See odm_execution.log."
                job.end_time = datetime.now()
                return job
                
        except Exception as e:
            job.status = "FAILED"
            job.error_info = f"Failed to execute Docker command: {str(e)}"
            job.end_time = datetime.now()
            return job
            
        # 5. Output Discovery
        # ODM output point cloud is usually at `odm_georeferencing/odm_georeferenced_model.ply`
        # or `odm_filterpoints/point_cloud.ply`
        expected_pc_path_geo = os.path.join(dataset_dir, "odm_georeferencing", "odm_georeferenced_model.ply")
        expected_pc_path_filter = os.path.join(dataset_dir, "odm_filterpoints", "point_cloud.ply")
        
        if os.path.exists(expected_pc_path_geo):
            job.generated_point_cloud_path = expected_pc_path_geo
            # Assuming if georeferenced output exists, it might have CRS (though PLY doesn't store CRS easily, metadata might)
            # Without reading ODM's specific metadata files, we conservatively flag it:
            # Proper CRS reading would parse `odm_georeferencing/odm_georeferenced_model.info`
            info_file = expected_pc_path_geo.replace(".ply", ".info")
            if os.path.exists(info_file):
                with open(info_file, 'r') as f:
                    job.crs_info = f.read().strip()
            else:
                job.crs_info = "PROBABLY GEOREFERENCED (MISSING .info)"
        elif os.path.exists(expected_pc_path_filter):
            job.generated_point_cloud_path = expected_pc_path_filter
            job.crs_info = "NOT GEOREFERENCED"
        else:
            job.status = "FAILED"
            job.error_info = "ODM completed but point cloud output could not be found."
            job.end_time = datetime.now()
            return job
            
        job.status = "SUCCESS"
        job.end_time = datetime.now()
        logger.info(f"ODM Job {job.job_id} completed successfully. Output: {job.generated_point_cloud_path}")
        return job
