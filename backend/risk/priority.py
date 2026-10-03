import pandas as pd
import numpy as np

def assign_priorities(df):
    print("Assigning priority zones and generating explanations...")
    
    p50 = df.groupby('date')['composite_risk_score'].transform(lambda x: x.quantile(0.50))
    p80 = df.groupby('date')['composite_risk_score'].transform(lambda x: x.quantile(0.80))
    p95 = df.groupby('date')['composite_risk_score'].transform(lambda x: x.quantile(0.95))
    
    conditions = [
        (df['composite_risk_score'] <= p50),
        (df['composite_risk_score'] > p50) & (df['composite_risk_score'] <= p80),
        (df['composite_risk_score'] > p80) & (df['composite_risk_score'] <= p95),
        (df['composite_risk_score'] > p95)
    ]
    choices = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
    
    df['priority_level'] = np.select(conditions, choices, default='LOW')
    
    # Priority rank: higher score = rank 1 (operational ordering)
    df['priority_rank'] = df.groupby('date')['composite_risk_score'].rank(method='min', ascending=False)
    
    # Generate risk explanations
    def generate_explanation(row):
        factors = []
        factors.append(f"Projected capacity utilization: {row['capacity_utilization']*100:.0f}%")
        
        if pd.notna(row.get('flood_exposure')) and row['flood_exposure'] > 0:
            factors.append(f"Flood exposure: {row['flood_exposure']:.2f}")
            
        if pd.notna(row.get('rainfall_7d')) and row['rainfall_7d'] > 0:
            factors.append(f"7-day rainfall: {row['rainfall_7d']:.1f} mm")
            
        if row.get('damage_risk_score', 0) > 0:
            factors.append("Historical damage frequency: elevated")
            
        exp = f"DPC {row['dpc_id']} | Composite Risk: {row['composite_risk_score']:.0f}\nMain contributors:\n- " + "\n- ".join(factors)
        return exp
        
    df['risk_explanation'] = df.apply(generate_explanation, axis=1)
    
    return df
