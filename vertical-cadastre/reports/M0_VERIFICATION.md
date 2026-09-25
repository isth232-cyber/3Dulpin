# M0 VERIFICATION REPORT

**Status:** PASS

## Environment
```json
{
  "python": {
    "version": "3.11.9",
    "pass": true
  },
  "open3d": true,
  "numpy": true,
  "scipy": true,
  "pytest": true
}
```

## Dataset
```json
{
  "generation": "PASS",
  "point_count": 50000,
  "building_dimensions": {
    "width": 15.0,
    "depth": 10.0,
    "height": 6.0
  },
  "overall_bounding_box": {
    "min": [
      -4.99986158310655,
      -4.999767304892677,
      0.0
    ],
    "max": [
      19.99812067082941,
      14.998019540184632,
      6.0
    ],
    "width": 24.997982253935962,
    "depth": 19.997786845077307,
    "height": 6.0
  }
}
```

## Processing
```json
{
  "loading": "PASS",
  "downsampling": {
    "operation": "voxel_downsampling",
    "parameters": {
      "voxel_size": 0.5
    },
    "input_points": 50000,
    "output_points": 4382,
    "reduction_ratio": 0.9123600000000001
  },
  "outlier_removal": {
    "operation": "statistical_outlier_removal",
    "parameters": {
      "nb_neighbors": 20,
      "std_ratio": 2.0
    },
    "input_points": 4382,
    "output_points": 4207,
    "reduction_ratio": 0.039936102236421744
  },
  "statistics": {
    "point_count": 4207,
    "min": {
      "x": -4.720017368607397,
      "y": -4.6963204978075765,
      "z": 0.0
    },
    "max": {
      "x": 19.690150466185543,
      "y": 14.780195609231418,
      "z": 6.0
    },
    "dimensions": {
      "width": 24.41016783479294,
      "depth": 19.476516107038996,
      "height": 6.0
    },
    "centroid": [
      7.489096091985985,
      5.002781024079561,
      2.1051479245645415
    ]
  }
}
```

## Tests
```json
{
  "total": 8,
  "passed": 8,
  "failed": 0,
  "status": "PASS"
}
```

