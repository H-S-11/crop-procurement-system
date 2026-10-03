"""
Storage Saturation & Operational Risk Engine.
Implements transparent stock flow modeling and interpretable rule-based risk classification.
All metrics are traceable to physical quantities, explicit assumptions, or labeled proxies.
"""
import numpy as np
import pandas as pd

OUTFLOW_ASSUMPTION_NOTE = "Assumption: Estimated outflow modeled at 10% capacity/day (TNCSC Godown B5 ledger is unlinked to individual DPCs)"

def calculate_storage_and_risk(df):
    """
    Computes:
    - Current Stock (MT) from recorded ledger or cumulative arrival/dispatch balance
    - Estimated Outflow (MT) over 3d/7d horizon under documented operational assumption
    - Projected Stock (MT) = Current Stock + Expected Arrivals - Estimated Outflow
    - Capacity Utilization (%) = Projected Stock / Capacity * 100
    - Overflow (MT) = max(0, Projected Stock - Capacity)
    - Interpretable Operational Risk Tiers (GREEN, YELLOW, RED, DARK_RED, OFF_SEASON)
    - Fact-based operational explanations
    """
    df = df.copy()
    
    # 1. Capacity
    df['capacity_mt'] = df['capacity'].fillna(100.0).astype(float)
    
    # 2. Current Stock on hand (MT)
    # Prefer recorded closing stock from B2 ledger if available; fallback to previous day projected stock
    if 'recorded_closing_stock_mt' in df.columns:
        df['current_stock_mt'] = df['recorded_closing_stock_mt'].fillna(0.0)
    else:
        df['current_stock_mt'] = 0.0
        
    # Ensure expected arrivals exist (from arrival forecaster or rolling baselines)
    if 'expected_arrival_1d_mt' not in df.columns:
        df['expected_arrival_1d_mt'] = df.get('arrival_3d_mean', 0.0).fillna(0.0)
    if 'expected_arrival_3d_mt' not in df.columns:
        df['expected_arrival_3d_mt'] = (df['expected_arrival_1d_mt'] * 3.0).round(1)
    if 'expected_arrival_7d_mt' not in df.columns:
        df['expected_arrival_7d_mt'] = (df.get('arrival_7d_mean', df['expected_arrival_1d_mt']) * 7.0).round(1)
        
    if 'arrival_trend' not in df.columns:
        df['arrival_trend'] = 'Stable'
    if 'arrival_surge_flag' not in df.columns:
        df['arrival_surge_flag'] = False

    # 3. Estimated Outflow over 3-day planning horizon
    # Standard operational clearance capacity assumption: 10% of DPC capacity per day
    daily_clearance_rate = df['capacity_mt'] * 0.10
    
    # 3-Day Estimated Outflow: limited by available stock + incoming arrivals
    avail_3d = df['current_stock_mt'] + df['expected_arrival_3d_mt']
    df['estimated_outflow_3d_mt'] = np.minimum(avail_3d, daily_clearance_rate * 3.0).round(1)
    
    # 7-Day Estimated Outflow
    avail_7d = df['current_stock_mt'] + df['expected_arrival_7d_mt']
    df['estimated_outflow_7d_mt'] = np.minimum(avail_7d, daily_clearance_rate * 7.0).round(1)

    # 4. Projected Stock = Current Stock + Expected Arrivals - Estimated Outflow
    df['projected_stock_3d_mt'] = np.maximum(0.0, df['current_stock_mt'] + df['expected_arrival_3d_mt'] - df['estimated_outflow_3d_mt']).round(1)
    df['projected_stock_7d_mt'] = np.maximum(0.0, df['current_stock_mt'] + df['expected_arrival_7d_mt'] - df['estimated_outflow_7d_mt']).round(1)
    
    # Primary operational projected stock (3-day decision horizon)
    df['projected_stock_mt'] = df['projected_stock_3d_mt']
    
    # 5. Capacity Utilization & Overflow Risk
    df['utilization_pct'] = np.where(
        df['capacity_mt'] > 0,
        np.round((df['projected_stock_mt'] / df['capacity_mt']) * 100.0, 1),
        0.0
    )
    df['utilization_pct'] = np.minimum(df['utilization_pct'], 100.0)
    df['overflow_mt'] = np.maximum(0.0, df['projected_stock_mt'] - df['capacity_mt']).round(1)
    
    # 6. Environmental and Access Measurable Indicators
    df['flood_exposure_pct'] = (df.get('flood_exposure', 0.0).fillna(0.0) * 100.0).round(1)
    df['rainfall_7d_mm'] = df.get('rainfall_7d', 0.0).fillna(0.0).round(1)
    df['access_disrupted'] = df.get('access_disruption', 0).fillna(0).astype(bool) | (df.get('nearest_road_dist', 500) > 1500)
    
    # Determine active procurement season status
    # A centre is active if it has arrivals, stock on hand, or is scheduled in the operational season
    df['is_active_season'] = (df['current_stock_mt'] > 0) | (df['arrival_mt'] > 0) | (df['expected_arrival_3d_mt'] > 0)
    
    # 7. Interpretable Operational Risk Tiers
    # GREEN: normal operations
    # YELLOW: needs monitoring
    # RED: high operational attention
    # DARK_RED: critical / multiple severe factors
    
    tiers = []
    explanations = []
    
    for _, row in df.iterrows():
        if not row['is_active_season']:
            tiers.append('OFF_SEASON')
            explanations.append(['Centre not operating in current harvest window'])
            continue
            
        util = row['utilization_pct']
        overflow = row['overflow_mt']
        flood_exp = row['flood_exposure_pct']
        rain7d = row['rainfall_7d_mm']
        access = row['access_disrupted']
        surge = row['arrival_surge_flag']
        exp_3d = row['expected_arrival_3d_mt']
        cap = row['capacity_mt']
        stock = row['projected_stock_mt']
        
        reasons = []
        if overflow > 0:
            reasons.append(f"Projected overflow: {overflow:.1f} MT above capacity ({cap:.0f} MT)")
        elif util >= 85:
            reasons.append(f"Near full: {util:.0f}% capacity utilization ({stock:.0f}/{cap:.0f} MT)")
        elif util >= 60:
            reasons.append(f"Moderate utilization: {util:.0f}% capacity ({stock:.0f}/{cap:.0f} MT)")
            
        if surge:
            reasons.append(f"Arrival surge detected: 3-day expectation {exp_3d:.1f} MT exceeds normal baseline")
        elif row['arrival_trend'] == 'Increasing':
            reasons.append(f"Increasing arrival trend: {exp_3d:.1f} MT expected over 3 days")
            
        if flood_exp >= 25:
            reasons.append(f"Elevated SAR flood exposure: {flood_exp:.0f}% standing water observed within 500m")
        elif flood_exp > 5:
            reasons.append(f"Low SAR flood exposure: {flood_exp:.0f}% standing water within 500m")
            
        if rain7d >= 70:
            reasons.append(f"Heavy 7-day rainfall: {rain7d:.1f} mm")
        elif rain7d >= 40:
            reasons.append(f"Moderate 7-day rainfall: {rain7d:.1f} mm")
            
        if access:
            reasons.append("Access corridor alert: potential route disruption or road closure nearby")
            
        # Multi-factor critical evaluation
        is_overflow = (overflow > 0) or (util >= 95.0)
        has_environmental_or_access = (flood_exp >= 15.0) or (access) or (rain7d >= 60.0) or surge
        
        if is_overflow and has_environmental_or_access:
            tier = 'DARK_RED'
        elif (util >= 85.0) or (overflow > 0) or (flood_exp >= 25.0) or (surge and util >= 65.0):
            tier = 'RED'
        elif (util >= 60.0) or (flood_exp >= 5.0) or (rain7d >= 40.0) or access or (row['arrival_trend'] == 'Increasing' and util >= 45.0):
            tier = 'YELLOW'
        else:
            tier = 'GREEN'
            if not reasons:
                reasons.append("Normal operations: adequate capacity, open access, clear weather")
                
        tiers.append(tier)
        explanations.append(reasons)
        
    df['risk_tier'] = tiers
    df['risk_explanation'] = explanations
    df['outflow_assumption_note'] = OUTFLOW_ASSUMPTION_NOTE
    
    # Calculate suggested alternatives for overflow cases
    df['suggested_alternatives'] = [[] for _ in range(len(df))]
    lat_col = 'latitude' if 'latitude' in df.columns else 'lat' if 'lat' in df.columns else None
    lon_col = 'longitude' if 'longitude' in df.columns else 'lon' if 'lon' in df.columns else None
    
    if lat_col and lon_col:
        # Precompute available capacity
        df['available_cap'] = np.maximum(0.0, df['capacity_mt'] - df['projected_stock_mt'])
        
        for idx, row in df.iterrows():
            if row['overflow_mt'] > 0 and row['is_active_season']:
                # Find valid candidates
                candidates = df[
                    (df.index != idx) & 
                    (df['is_active_season']) & 
                    (df['available_cap'] > 0)
                ].copy()
                
                if not candidates.empty:
                    # Calculate distances
                    lat1 = np.radians(row[lat_col])
                    lon1 = np.radians(row[lon_col])
                    lat2 = np.radians(candidates[lat_col])
                    lon2 = np.radians(candidates[lon_col])
                    
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                    c = 2 * np.arcsin(np.sqrt(a))
                    r = 6371  # Radius of earth in kilometers
                    candidates['dist_km'] = c * r
                    
                    top3 = candidates.sort_values('dist_km').head(3)
                    alts = []
                    for _, alt in top3.iterrows():
                        alts.append({
                            'id': alt['id'] if 'id' in alt else alt.get('dpc_id', ''),
                            'name': alt.get('name', alt.get('dpc_name', '')),
                            'distance_km': round(alt['dist_km'], 1),
                            'available_capacity_mt': round(alt['available_cap'], 1)
                        })
                    df.at[idx, 'suggested_alternatives'] = alts

    return df
