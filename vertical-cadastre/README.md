# Vertical Cadastre System

A research-grade prototype for 3D ULPIN Generation and Vertical Property Mapping System (SIH26011).

This project focuses on converting physical properties into georeferenced, structured 3D digital property representations, validating cadastral topology, and persisting a vertical property identity linked to the parent parcel ULPIN.

## Current Milestone: M0 - DEVELOPMENT FOUNDATION
The foundational architecture, logging, basic point cloud loading, and verification frameworks have been established.

## Setup Instructions

1. Clone the repository.
2. Ensure you have Python 3.11+ installed.
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Generate Synthetic Data
To generate a deterministic synthetic multi-floor building point cloud for testing:
```bash
python scripts/generate_test_data.py
```
This saves data to `data/synthetic/building.ply` and `_metadata.json`.

### Run Preprocessing and Validation
To run the automated verification for M0, which includes data generation, loading, downsampling, outlier removal, statistics, and tests:
```bash
python scripts/verify.py
```

### Run Tests Directly
```bash
pytest tests/unit/
```

## Project Structure

Refer to `ARCHITECTURE.md` for detailed information on the module layout, and `VALIDATION.md` for our verification processes.
