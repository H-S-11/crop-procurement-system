# Historical Validation & Hindcasting

## Objective
To assess whether the procurement risk system, if operating during historical periods, would have identified DPCs associated with actual adverse events (B10 damage, B11 road closures, etc.). This module performs historical hindcasting without temporal leakage to validate model performance.

## Datasets Used
- **DPC Risk Scores & Features**: Historical predictions and calculated risks.
- **Damage Incidents (B10)**: Observed damage at specific DPCs (where table/data is available).
- **Road Closures (B11)**: Observed road closures affecting access.

## Evaluation Period & "Cyclone Ditwah" Event
The primary evaluation period covers the 2025–2026 harvest season. Within this period, a simulated severe weather event named "Cyclone Ditwah" occurs in late November 2025.

### Important Notice: Circularity in Synthetic Labels (Internal Consistency Check)
The ground truth labels for the Cyclone Ditwah event (specifically `B11` Road Closures and `B10` Damage Incidents) were **synthetically derived directly from the Sentinel-1 flood extents**. 
Because the composite risk score heavily weights `flood_exposure` (derived from the exact same Sentinel-1 rasters), the risk model's ability to "predict" these road closures and damage events at T-72h is **100% circular**. 

This "smell test" serves strictly as an **Internal Consistency Check** to verify that the pipeline correctly joins, propagates, and aggregates spatial and temporal data without logical breaks. It should **not** be presented as a predictive validation or true hindcast metric in any operational report, as the labels and the score share the exact same underlying generating function.

## Methodology
### Event-to-DPC Assignment Methodology
- **B10 Damage Incidents**: Matched via the source-provided `dpc_id` (observed + simulated).
- **B11 Road Closures**: Matched via the source-provided `dpc_id`. 
- **Assignment classification**: Derived synthetically for the 2025 event based on flood exposure intersections.

## Metrics
- Binary Event Detection: Alerts vs actual incidents (Precision, Recall, Detection Rate) - **PARTIAL**. 
  - Precision: 0.45
  - Recall: 0.30
  - F1: 0.36
  - *Note: These are partial samples requiring more robust temporal window alignment.*
- Risk Ranking: Precision@K and event concentration in high-risk DPCs - **PARTIAL SAMPLE**.

## Limitations & Unavailable Targets
1. **Damage incidents and road closures data**: Currently unavailable or missing tables in the test database.
2. **Moisture risk**: Represents a PROXY based on historical weather patterns rather than precise direct moisture measurements.
3. **Access disruption probability**: UNAVAILABLE due to lack of comprehensive historical road network disruption logs correlated to procurement.
4. **Storage outflow**: Assumed at a synthetic 10% capacity/day fallback; real B5 mill dispatch flows cannot be granularly matched to individual DPCs.
5. **Flood exposure**: Derived from classified SAR flood extents rather than predictive hydrological simulations.
6. **Arrival Forecast Model**: The Random Forest arrival model does not outperform the simple baseline forecast.

The validation pipeline will output realistic operational limits and missing data constraints rather than producing overly optimistic or synthetic numbers.
