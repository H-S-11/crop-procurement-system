# Module 4: Storage Saturation + Composite Risk Engine

## Overview
This risk engine calculates a daily priority score per DPC to identify storage overflow and procurement disruption risks.

## Formulas & Assumptions
- **Projected Stock** = `current_stock + forecast_arrivals - estimated_outflow`
- **Estimated Outflow**: Assumed as 10% of capacity per day as a fallback. An attempt was made to derive exact outflow from the B5 Godown/Mill Ledger, but B5 aggregates `paddy_received_mt` exclusively at the Godown level (node_type='TNCSC Godown'). Distributing these aggregated Godown receipts back to individual DPCs without ground truth attribution would require fabricating an arbitrary mapping, which is strictly prohibited. Therefore, the fallback assumption is retained.
- **Capacity Utilization** = `projected_stock / available_capacity`
- **Storage Risk Score**: `Capacity Utilization * 100` (capped at 100)

## Composite Weights
- Storage (40%), Flood (20%), Weather (20%), Damage (10%), Access (10%)
- Found in `backend/config/risk_weights.json`

## Priority Thresholds
- LOW: < 30
- MODERATE: 30-59
- HIGH: 60-79
- CRITICAL: >= 80

## Limitations & Validation
- Moisture data absent; risk is proxied via 14-day rainfall and flood exposure.
- Access disruption classifier unavailable due to lack of ground truth labels.
- Historical validation against B10 damage incidents is pending integration of damage locations.
