# Crop Procurement Forecasting - Project Summary

## Objective & Problem Scope
This project aims to supply decision support for the Thanjavur paddy procurement process. Sudden influxes of crop yield alongside unexpected weather and logistics blockages cause crop damage and supply chain issues. The system evaluates DPCs (Direct Procurement Centres) for vulnerabilities.

## Scope & Datasets
- Centered strictly on Thanjavur district.
- Integrates master DPC geospatial points, arrival histories, mill logistics, consumables inventories, historical road closures, and damage incident registries.
- **Note:** Real-time geospatial APIs and exact dispatch trackers (B5 datasets) lack fine-grained data per DPC and required synthetic scaling/matching assumptions during development.

## Methodology & Risk Scoring
- Features aggregated temporally using rolling window metrics (e.g. 7-day, 14-day rainfall and arrival averages).
- The engine computes normalized vulnerability variables against storage capabilities (capacity_mt) and environmental threats (flood_exposure).
- The composite risk assigns priorities: CRITICAL, HIGH, MODERATE, LOW.

## Validation & Results
A strictly controlled validation pipeline evaluates historical data against the alert thresholds.
- **Arrival Model:** The machine-learning Random Forest currently does not natively outperform simpler rolling-average baselines.
- **Alert Precision/Recall:** The detection logic achieved a partial precision mapping of 0.45 and a recall of 0.30 due strictly to limited dataset scopes and coarse temporal granularity.

## System Limitations
1. Moisture index is solely a derived atmospheric proxy rather than real on-site measurements.
2. Road network blockages mapping uses broad geographical assignments and lacks dynamic disruption probability forecasts.
3. Godown dispatch outflows are structurally constrained to a 10% daily synthetic capability instead of actual measured capacity.
4. Flood exposure leverages classified SAR arrays instead of a fully predictive hydrological mechanism.
5. Base prototypes use SQLite and are functionally limited spatially when compared to the intended PostGIS deployment.

## Future Improvements
- Upgrade the database to PostGIS for improved spatial aggregations.
- Ingest real-world B5 mill dispatch flows at the individual DPC level.
- Establish IoT moisture sensing mapping.
- Train advanced temporal-spatial neural networks once robust B10 damage incidents reach sufficient statistical thresholds.
