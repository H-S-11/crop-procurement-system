# Alert Engine Documentation

The Alert Engine runs daily to evaluate conditions across all DPCs and generates alerts based on configurable thresholds.

## Alert Types and Rules

1. **HIGH_RISK_DPC**: Triggered when a DPC's composite risk score reaches the configured `high_risk_score` (MODERATE -> HIGH transition) or `critical_risk_score` (HIGH -> CRITICAL transition).
2. **STORAGE_SATURATION**: Triggered when projected storage utilization (including 10% daily outflow fallback) exceeds `storage_saturation_pct`.
3. **FLOOD_EXPOSURE**: Triggered when a DPC is exposed to flooding (derived from SAR flood classification).
4. **HEAVY_RAINFALL**: Triggered when observed 1-day rainfall exceeds `heavy_rainfall_1d_mm`.
5. **ARRIVAL_SURGE**: (Future) Triggered when forecast arrivals significantly exceed historical baselines. Currently UNAVAILABLE due to insufficient reliable comparative data.

## Configuration

Thresholds are stored in `backend/config/alert_thresholds.json`.

- `storage_saturation_pct`: Percentage of capacity (default: 80)
- `high_risk_score`: Score to trigger HIGH alert (default: 70)
- `critical_risk_score`: Score to trigger CRITICAL alert (default: 85)
- `heavy_rainfall_1d_mm`: Millimeters of rain in 24h (default: 50)

## Deduplication and State Management

- Alerts have a status of `ACTIVE` or `RESOLVED`.
- When an evaluation runs, if an existing condition is still met, the `event_date` and values are updated but the alert remains `ACTIVE`. 
- Multiple instances of the same alert type for the same DPC are NOT created.
- If a previously `ACTIVE` alert's condition is no longer met in the current evaluation, its status is changed to `RESOLVED`.

## Limitations
- Flood exposure relies on classified satellite imagery and does not predict future flooding accurately.
- Storage projections use a static 10% outflow assumption because precise mill-dispatch data (B5) cannot be mapped per DPC.
- Alerts are generated deterministically based on data; no subjective or AI-generated severity is applied.
