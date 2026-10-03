import pandas as pd
from sqlalchemy import create_engine
import os

def verify_risk():
    db_url = os.getenv('DATABASE_URL', 'sqlite:///../data/paddy_db.sqlite')
    engine = create_engine(db_url)
    
    print("Verifying Risk Engine Output...")
    try:
        df = pd.read_sql("SELECT * FROM dpc_risk_scores", engine)
    except Exception as e:
        print("dpc_risk_scores table not found or error reading:", e)
        return
        
    print(f"Total Rows: {len(df)}")
    if len(df) == 0:
        print("FAILED: Risk score table is empty")
        return
        
    # Scores are 0-100
    for col in ['storage_risk_score', 'flood_risk_score', 'weather_risk_score', 'composite_risk_score']:
        if (df[col] < 0).any() or (df[col] > 100).any():
            print(f"FAILED: {col} is out of bounds (0-100).")
        else:
            print(f"OK: {col} is within 0-100 bounds.")
            
    # Projected stock non-negative
    if (df['projected_stock_mt'] < 0).any():
        print("FAILED: projected_stock_mt contains negative values.")
    else:
        print("OK: projected_stock_mt is non-negative.")
        
    # Overflow non-negative
    if (df['overflow_mt'] < 0).any():
        print("FAILED: overflow_mt contains negative values.")
    else:
        print("OK: overflow_mt is non-negative.")
        
    # No missing DPCs
    if df['dpc_id'].isnull().any():
        print("FAILED: Missing DPC IDs.")
    else:
        print("OK: No missing DPC IDs.")
        
    # No duplicate DPC/date
    if df.duplicated(subset=['dpc_id', 'date']).any():
        print("FAILED: Duplicates found for DPC/date.")
    else:
        print("OK: No duplicate DPC/date records.")
        
    # Future data leakage check
    # We check if there's any date from the future
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].max() > pd.Timestamp.now():
        print("WARNING: Future dates found in risk records.")
    else:
        print("OK: No future leakage detected.")
        
    # Check priority distribution
    counts = df['priority_level'].value_counts()
    print(f"Priority Distribution:\n{counts}")
    
    print("Risk Engine verification complete.")

if __name__ == '__main__':
    verify_risk()
