# System Architecture

The Crop Procurement Forecasting system is designed as an operational data processing, risk scoring, and dashboarding engine.

## Complete Data Flow

`Data Sources` &rarr; `Preprocessing Engine` &rarr; `Forecasting / Risk Engine` &rarr; `Alert Engine` &rarr; `FastAPI Backend` &rarr; `Next.js Frontend` &rarr; `Validation (Hindcast)`

### 1. Data Sources
- Master DPC Layer (Points)
- Daily Arrival Ledgers
- Godown / Mill Ledgers
- Consumables Inventory
- Weather & Rain Observations
- Historical Incident Logs

### 2. Preprocessing & Database Engine
- Python ingestion scripts transform CSV datasets into a relational structure.
- Core spatial interactions and features are pushed to a SQLite database (`paddy_db.sqlite`).
- The `DPCFeatureStore` aggregates features (weather, distance, closures) temporally per DPC.

### 3. Forecasting & Risk Module
- **Arrivals Model**: Analyzes rolling averages and temporal shifts using Random Forest (note: baseline rolling-mean performs comparably or better).
- **Storage Saturation**: Assumes a synthetic 10% daily outflow based on capacity.
- **Risk Aggregator**: Computes a normalized composite score factoring in damage risk and storage risks.

### 4. Alert Engine
- Reads evaluated thresholds (`alert_thresholds.json`).
- Translates dynamic risk conditions (HIGH, CRITICAL) into categorized actionable alerts (STORAGE_SATURATION, HEAVY_RAINFALL, FLOOD_EXPOSURE, HIGH_RISK_DPC).
- Reduces duplicate notifications efficiently.

### 5. FastAPI Backend
- Supplies RESTful endpoints to query evaluated risks, alerts, validation results, and historical summaries.
- Validates payload typing strictly via Pydantic.

### 6. Next.js Frontend
- Uses React, TailwindCSS, and MapLibre GL for the visualization tier.
- Integrates interactive map selections bound directly to the DPC-specific alerting system.

### 7. Validation Pipeline
- Prevents temporal data leakage through the strictly constrained `hindcast.py` methodology.
- Verifies model detection capabilities against raw B10 (Damage) and B11 (Road closures) historically logged events.
