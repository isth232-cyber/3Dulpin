import os
import sys
import json
import time
import subprocess
from importlib.util import find_spec

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_test_data import generate_synthetic_building
from pipeline.preprocessing.loader import load_point_cloud
from pipeline.preprocessing.filters import voxel_downsample, remove_statistical_outliers
from pipeline.preprocessing.stats import calculate_statistics

def verify_m0():
    print("="*40)
    print("VERTICAL CADASTRE — M0 VERIFICATION")
    print("="*40 + "\n")
    
    start_time = time.time()
    
    report_data = {
        "milestone": "M0",
        "status": "FAIL",
        "environment": {},
        "dataset": {},
        "processing": {},
        "tests": {},
        "execution_time": {}
    }
    
    # Environment
    print("Environment")
    
    env_passed = True
    
    py_version = sys.version.split()[0]
    py_pass = sys.version_info >= (3, 11)
    print(f"{'PASS' if py_pass else 'FAIL':<19} Python {py_version}")
    report_data["environment"]["python"] = {"version": py_version, "pass": py_pass}
    env_passed = env_passed and py_pass
    
    # Core dependencies for M0
    # Note: 'torch' is omitted from M0 strict dependency verification.
    # While PyTorch is in the overall technology plan for future AI semantic segmentation (M6), 
    # M0's point-cloud processing and foundation strictly rely on Open3D, NumPy, and SciPy.
    # Therefore, M0 does not falsely depend on future AI functionality.
    for pkg in ["open3d", "numpy", "scipy", "pytest"]:
        passed = find_spec(pkg) is not None
        print(f"{'PASS' if passed else 'FAIL':<19} {pkg}")
        report_data["environment"][pkg] = passed
        env_passed = env_passed and passed
        
    print()
    
    # Dataset
    print("Synthetic Dataset")
    ds_passed = True
    ds_file = "data/synthetic/verify_building.ply"
    
    try:
        if os.path.exists(ds_file):
            os.remove(ds_file)
        meta = generate_synthetic_building(ds_file, num_floors=2, width=15.0, depth=10.0, floor_height=3.0, points_per_sqm=50, seed=42)
        print(f"{'PASS':<19} Generation")
        report_data["dataset"]["generation"] = "PASS"
        
        print(f"{meta['num_points']:<19} Point Count")
        report_data["dataset"]["point_count"] = meta['num_points']
        
        b_dims = meta['building_dimensions']
        print(f"{b_dims['width']} × {b_dims['depth']} × {b_dims['height']:<7} Building Dimensions")
        report_data["dataset"]["building_dimensions"] = b_dims
        
        o_dims = meta['overall_bounding_box']
        print(f"{o_dims['width']} × {o_dims['depth']} × {o_dims['height']:<7} Point Cloud Bounding Box")
        report_data["dataset"]["overall_bounding_box"] = o_dims
    except Exception as e:
        print(f"{'FAIL':<19} Generation ({e})")
        report_data["dataset"]["generation"] = f"FAIL: {e}"
        ds_passed = False
        
    print()
    
    # Processing
    print("Processing")
    proc_passed = True
    
    try:
        pcd, load_meta = load_point_cloud(ds_file)
        print(f"{'PASS':<19} Loading")
        report_data["processing"]["loading"] = "PASS"
        
        ds_pcd, ds_info = voxel_downsample(pcd, voxel_size=0.5)
        print(f"{'PASS':<19} Downsampling")
        report_data["processing"]["downsampling"] = ds_info
        
        out_pcd, out_info = remove_statistical_outliers(ds_pcd, nb_neighbors=20, std_ratio=2.0)
        print(f"{'PASS':<19} Outlier Removal")
        report_data["processing"]["outlier_removal"] = out_info
        
        stats = calculate_statistics(out_pcd)
        print(f"{'PASS':<19} Statistics")
        report_data["processing"]["statistics"] = stats
        
        # Save processed
        out_file = "data/processed/verify_building_processed.ply"
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        import open3d as o3d
        o3d.io.write_point_cloud(out_file, out_pcd)
        
    except Exception as e:
        print(f"{'FAIL':<19} Processing ({e})")
        report_data["processing"]["status"] = f"FAIL: {e}"
        proc_passed = False
        
    print()
    
    # Tests
    print("Tests")
    test_passed = True
    
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/unit/test_m0.py", "-v"], capture_output=True, text=True)
        if result.returncode == 0:
            output_lines = result.stdout.split('\n')
            total = sum(1 for line in output_lines if "PASSED" in line)
            print(f"{total:<19} Total")
            print(f"{total:<19} Passed")
            print(f"{0:<19} Failed")
            report_data["tests"] = {"total": total, "passed": total, "failed": 0, "status": "PASS"}
        else:
            print(f"{'FAIL':<19} Pytest Execution Failed")
            print(result.stdout)
            report_data["tests"] = {"status": "FAIL", "output": result.stdout}
            test_passed = False
    except Exception as e:
        print(f"{'FAIL':<19} Pytest Error ({e})")
        report_data["tests"] = {"status": f"FAIL: {e}"}
        test_passed = False
        
    print()
    
    # Overall
    overall_pass = env_passed and ds_passed and proc_passed and test_passed
    report_data["status"] = "PASS" if overall_pass else "FAIL"
    
    end_time = time.time()
    report_data["execution_time"]["total_seconds"] = end_time - start_time
    
    print(f"Overall Result: {'PASS' if overall_pass else 'FAIL'}")
    print("="*40)
    
    # Write reports
    os.makedirs("reports", exist_ok=True)
    with open("reports/m0_verification.json", "w") as f:
        json.dump(report_data, f, indent=2)
        
    with open("reports/M0_VERIFICATION.md", "w") as f:
        f.write("# M0 VERIFICATION REPORT\n\n")
        f.write(f"**Status:** {'PASS' if overall_pass else 'FAIL'}\n\n")
        f.write("## Environment\n")
        f.write("```json\n" + json.dumps(report_data["environment"], indent=2) + "\n```\n\n")
        f.write("## Dataset\n")
        f.write("```json\n" + json.dumps(report_data["dataset"], indent=2) + "\n```\n\n")
        f.write("## Processing\n")
        f.write("```json\n" + json.dumps(report_data["processing"], indent=2) + "\n```\n\n")
        f.write("## Tests\n")
        f.write("```json\n" + json.dumps(report_data["tests"], indent=2) + "\n```\n\n")
        
    if not overall_pass:
        sys.exit(1)

def verify_m1():
    print("="*40)
    print("VERTICAL CADASTRE — M1 VERIFICATION")
    print("="*40 + "\n")
    
    start_time = time.time()
    report_data = {
        "milestone": "M1",
        "status": "FAIL",
        "environment": {},
        "odm": {},
        "tests": {},
        "execution_time": {}
    }
    
    # Environment
    print("Environment")
    env_passed = True
    
    py_pass = sys.version_info >= (3, 11)
    print(f"{'PASS' if py_pass else 'FAIL':<19} Python")
    report_data["environment"]["python"] = py_pass
    env_passed = env_passed and py_pass
    
    for pkg in ["open3d", "numpy"]:
        passed = find_spec(pkg) is not None
        print(f"{'PASS' if passed else 'FAIL':<19} {pkg}")
        report_data["environment"][pkg] = passed
        env_passed = env_passed and passed
        
    try:
        res = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        docker_pass = res.returncode == 0
    except:
        docker_pass = False
    print(f"{'PASS' if docker_pass else 'FAIL':<19} Docker")
    report_data["environment"]["docker"] = docker_pass
    env_passed = env_passed and docker_pass
    
    print()
    
    # Tests
    print("Tests")
    test_passed = True
    
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/unit/test_m1.py", "tests/integration/test_m1_odm.py", "-v"], capture_output=True, text=True)
        
        output_lines = result.stdout.split('\n')
        passed_count = sum(1 for line in output_lines if "PASSED" in line)
        failed_count = sum(1 for line in output_lines if "FAILED" in line)
        skipped_count = sum(1 for line in output_lines if "SKIPPED" in line)
        
        # Integration test might be skipped if no real data
        total_m1_tests = passed_count + failed_count + skipped_count
        
        print(f"{total_m1_tests:<19} Total")
        print(f"{passed_count:<19} Passed")
        print(f"{failed_count:<19} Failed")
        print(f"{skipped_count:<19} Skipped")
        
        real_data_status = "PENDING" if skipped_count > 0 else ("FAIL" if failed_count > 0 else "PASS")
        print(f"\nREAL DATA VALIDATION: {real_data_status}")
        
        if failed_count > 0 or result.returncode not in (0, 5): # pytest returns 5 if no tests collected, but here we expect some
            print(f"{'FAIL':<19} Pytest Execution Failed")
            report_data["tests"] = {"status": "FAIL", "output": result.stdout}
            test_passed = False
        else:
            report_data["tests"] = {"total": total_m1_tests, "passed": passed_count, "failed": failed_count, "skipped": skipped_count, "real_data_validation": real_data_status, "status": "PASS"}
            
    except Exception as e:
        print(f"{'FAIL':<19} Pytest Error ({e})")
        report_data["tests"] = {"status": f"FAIL: {e}"}
        test_passed = False
        
    print()
    
    overall_pass = env_passed and test_passed
    report_data["status"] = "PASS" if overall_pass else "FAIL"
    
    end_time = time.time()
    report_data["execution_time"]["total_seconds"] = end_time - start_time
    
    print(f"Overall Result: {'PASS' if overall_pass else 'FAIL'}")
    print("="*40)
    
    # Write reports
    os.makedirs("reports", exist_ok=True)
    with open("reports/m1_verification.json", "w") as f:
        json.dump(report_data, f, indent=2)
        
    with open("reports/M1_VERIFICATION.md", "w") as f:
        f.write("# M1 VERIFICATION REPORT\n\n")
        f.write(f"**Status:** {'PASS' if overall_pass else 'FAIL'}\n\n")
        f.write(f"**REAL DATA VALIDATION:** {report_data['tests'].get('real_data_validation', 'UNKNOWN')}\n\n")
        f.write("## Environment\n")
        f.write("```json\n" + json.dumps(report_data["environment"], indent=2) + "\n```\n\n")
        f.write("## Tests\n")
        f.write("```json\n" + json.dumps(report_data["tests"], indent=2) + "\n```\n\n")
        
    if not overall_pass:
        sys.exit(1)

if __name__ == "__main__":
    verify_m0()
    verify_m1()
