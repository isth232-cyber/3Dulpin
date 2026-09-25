# Validation Framework

This project follows a strict "validate-first" philosophy. No feature is marked complete until it has numerical and measurable verification logic.

## M0 Validation

The M0 verification process focuses on ensuring the development foundation is solid.

The verification script (`scripts/verify.py`) does the following:
1. **Environment Check**: Verifies Python 3.11+ and checks for `open3d`, `numpy`, `scipy`, and `pytest`.
2. **Synthetic Data**: Runs `scripts/generate_test_data.py` to deterministically create a 3D synthetic building point cloud, tracking the points count and bounded dimensions.
3. **Processing Check**:
   - Tests point cloud loading.
   - Tests Voxel Downsampling and records input/output point counts.
   - Tests Statistical Outlier Removal and records point counts.
   - Computes point cloud statistics (centroid, bounding box dimensions, min/max).
4. **Unit Tests**: Runs the `pytest` suite ensuring all core algorithms act deterministically and handle invalid files gracefully.
5. **Reporting**: Generates structured reports in `reports/m0_verification.json` and `reports/M0_VERIFICATION.md` detailing all metrics.

A failure in any of these steps results in a non-zero exit code and failure report, blocking progress.
