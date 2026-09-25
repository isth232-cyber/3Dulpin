# Vertical Cadastre Roadmap

## M0 — DEVELOPMENT FOUNDATION (Current)
- Repository setup
- Environment configuration
- Testing and verification framework
- Synthetic test-data generator

## M1 — POINT CLOUD FOUNDATION
- Point cloud loading, visualization, and preprocessing
- Downsampling and outlier removal

## M2 — EXTERIOR PHOTOGRAMMETRY
- OpenDroneMap integration
- Pipeline: Images -> Point Cloud

## M3 — INTERIOR LiDAR
- Processing indoor LiDAR
- Cleaning and noise filtering

## M4 — EXTERIOR + INTERIOR REGISTRATION
- Initial alignment and global registration
- ICP refinement
- Unified coordinate system output

## M5 — POINT CLOUD FUSION
- Unified 3D building point cloud
- Duplicate handling and overlap resolution

## M6 — AI SEMANTIC SEGMENTATION
- PointNet++ baseline
- Semantic classification of structural elements

## M7 — FLOOR DETECTION
- Extract floor elevations using AI semantics and geometry

## M8 — 3D PROPERTY VOLUMES
- Represent properties as 3D volumes
- Boundaries, area, volume calculations

## M9 — TOPOLOGY VALIDATION
- Validate overlapping properties, gaps, and disconnected geometry

## M10 — VERTICAL PROPERTY IDENTITY
- Prototype ID generation linked to parent ULPIN

## M11 — DATABASE
- Spatial database integration (PostGIS)

## M12 — 3D WEB VIEWER
- Visualization of 3D models and cadastral data

## M13 — CHANGE DETECTION
- Comparing surveys and generating change reports

## M14 — END-TO-END DEMONSTRATION
- Final end-to-end pipeline execution from drone data to 3D Viewer
