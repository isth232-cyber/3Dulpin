# Vertical Cadastre Architecture

This system follows a modular architecture that cleanly separates data ingestion, physical processing, semantic segmentation, legal cadastral boundary extraction, and data persistence.

## System Layout

```
vertical-cadastre/
│
├── data/               # Storage for raw, processed, and synthetic data
├── pipeline/           # The core execution pipeline
│   ├── photogrammetry/ # Drone imagery to exterior point clouds
│   ├── lidar/          # Indoor LiDAR processing
│   ├── registration/   # Exterior and interior point cloud alignment
│   ├── fusion/         # Combining aligned point clouds
│   ├── preprocessing/  # Noise removal, downsampling
│   ├── segmentation/   # AI-based semantic segmentation (e.g., PointNet++)
│   ├── floors/         # Floor detection from semantics and geometry
│   ├── properties/     # 3D property volume generation
│   ├── topology/       # Validating 3D cadastral relationships
│   ├── identity/       # Vertical property ID linked to ULPIN
│   └── change_detection/# Temporal differences between surveys
├── models/             # ML model weights and architectures
├── database/           # Spatial database integrations
├── api/                # REST API for front-end integration
├── frontend/           # 3D web visualization
├── tests/              # Unit, integration, and end-to-end tests
├── validation/         # Validation logic and metrics calculation
├── scripts/            # Executable scripts (e.g., verify, run_pipeline)
└── reports/            # Output verification reports
```

## Technology Stack

- **Core Language**: Python 3.11+
- **Point Cloud Processing**: Open3D, NumPy, SciPy
- **Machine Learning**: PyTorch (PointNet++ baseline, ready for Point Transformer V3)
- **Photogrammetry**: OpenDroneMap (External Engine integration)
- **Database**: PostgreSQL with PostGIS / 3D spatial extensions (future)
- **Frontend**: WebGL / Three.js / Cesium (future)

## Design Principles

1. **Abstraction**: External tools like ODM are wrapped in interfaces so they can be replaced.
2. **Measurability**: Every step outputs measurable validation metrics (e.g., RMSE, IoU, bounding boxes).
3. **Reproducibility**: Rely heavily on automated testing and synthetic datasets.
