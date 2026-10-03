# Module 2: Spatial Preprocessing & Feature Engineering

## Objective
Convert raw geospatial and operational data into a reproducible DPC-level feature store (`dpc_feature_store`) suitable for consumption by forecasting models.

## Pipeline Structure
The preprocessing pipeline is located in `backend/pipelines/` and is orchestrated by `run_preprocessing.py`.

* **`spatial_features.py`**: Extracts DPC coordinates, village, block, and elevation data.
* **`road_features.py`**: Performs spatial joins against OSM road networks to compute nearest road distance, major road distance, and local road densities (1km, 5km). Reprojects geometries to EPSG:32644 (UTM 44N) for accurate metric measurements.
* **`flood_features.py`**: Given that Sentinel-1 data comprises raw/processed SAR rasters rather than classified flood masks, we currently record flood exposure as 0 and document this limitation to avoid fabricating data.
* **`rainfall_features.py`**: Joins DPCs to their nearest rainfall station via spatial proximity and aggregates historical daily rainfall into rolling 3-day, 7-day, 14-day, and 30-day accumulations, along with rainy days count.
* **`arrival_features.py`**: Aggregates daily arrivals from the B2 ledger into rolling means (7d, 14d), 7d max, and arrival volatility to capture procurement dynamics.

## Feature Store (`dpc_feature_store`)
The output is a time-aware panel dataset containing a daily record for each DPC. 
Features are strictly computed using information available up to the given `date` to prevent future leakage.

## QA and Reproducibility
* `run_preprocessing.py` can be re-run idempotently.
* `scripts/verify_features.py` validates the generated table for duplicates, bounds, nulls, negative values, and temporal leakage.
