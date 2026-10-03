# Data Ingestion Report (Module 1)

## Status
- **Database Setup Status:** Pending (Docker is unavailable in the execution environment)
- **Migration Status:** Pending (`alembic upgrade head` relies on the database being active)

## Datasets Configured for Load
- **B1_DPC_master_layer_Thanjavur.csv** -> `dpcs`
- **B2_daily_arrivals_Thanjavur.csv** -> `arrivals`
- **B5_godown_mill_ledger_Thanjavur.csv** -> `godown_ledger`
- **B7_consumables_inventory_Thanjavur.csv** -> `inventory_gunny_tarpaulin`
- **B10_damage_incident_register_Thanjavur.csv** -> `damage_incidents`
- **B11_road_closure_events_Thanjavur.csv** -> `road_closures`
- **thanjavur_boundaries.geojson** -> `villages`
- **planet_78.80,9.85_79.58,11.20.gpkg** -> `roads`
- **Sentinel-1 Rasters** -> `sar_flood_rasters` (metadata)
- **rainfall_observations.csv** -> `rainfall_observations`
- **data_provenance.csv** -> `data_provenance`

## Expected vs Actual Counts
*Actual counts are pending DB execution. The pipeline includes `verify_load.py` which will output these.*

- **B1 DPC master:** Expected 483
- **B2 daily arrivals:** Expected 61,426
- **B5 godown/mill ledger:** Expected 2,834
- **B7 consumables inventory:** Expected 61,426
- **B10 damage incidents:** Expected 170
- **B11 road closures:** Expected 4,984

## Spatial/CRS Validation Strategy
- **Standardized Storage:** All geometries are stored in `EPSG:4326` using GeoAlchemy2/PostGIS.
- **DPCs / Rainfall:** Pandas generates WKT (`POINT(lon lat)`) strings which are inserted natively.
- **Villages:** `json` parses the GeoJSON and inserts it via `ST_GeomFromGeoJSON`.
- **Roads:** `sqlite3` reads the GeoPackage blob, strips the 8-64 byte header to extract raw WKB, and inserts it via `ST_GeomFromWKB`.
- **Metric Projections:** Code comments in models remind that metric distance functions should cast to `EPSG:32644`.

## Issues Fixed
- Removed `geopandas` and `shapely` dependencies which are incompatible with Python 3.15 without MSVC C++ Build Tools.
- Abstracted spatial logic into native Python modules (`json` / `sqlite3`) and deferred spatial construction to the PostGIS database.

## Remaining Docker-Dependent Commands
The following commands must be run on an environment where Docker is available:
```bash
docker compose up -d
docker ps

# Initialize Alembic migrations
cd backend
.\venv\Scripts\alembic.exe revision --autogenerate -m "Init"
.\venv\Scripts\alembic.exe upgrade head

# Run Pipeline
.\venv\Scripts\python.exe scripts/load_all.py
.\venv\Scripts\python.exe scripts/verify_load.py
```
