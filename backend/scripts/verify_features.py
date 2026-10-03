import pandas as pd
from sqlalchemy import create_engine
import os

def verify_features():
    db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db')
    engine = create_engine(db_url)
    
    print("Verifying Feature Store...")
    try:
        df = pd.read_sql("SELECT * FROM dpc_feature_store", engine)
    except Exception as e:
        print("Feature store table not found or error reading:", e)
        return
        
    print(f"Total Rows: {len(df)}")
    if len(df) == 0:
        print("FAILED: Feature store is empty")
        return
        
    print(f"Total Unique DPCs: {df['dpc_id'].nunique()}")
    
    # Check for missing values in critical columns
    critical_cols = ['dpc_id', 'date', 'longitude', 'latitude']
    for col in critical_cols:
        missing = df[col].isnull().sum()
        if missing > 0:
            print(f"WARNING: {missing} missing values in {col}")
        else:
            print(f"OK: No missing values in {col}")
            
    # Check bounds (Thanjavur roughly)
    invalid_coords = df[(df['latitude'] < 8) | (df['latitude'] > 12) | (df['longitude'] < 78) | (df['longitude'] > 80)]
    if not invalid_coords.empty:
        print(f"WARNING: {len(invalid_coords)} rows have coordinates outside expected Thanjavur bounds.")
    else:
        print("OK: All coordinates within expected bounds.")
        
    # Check negative arrivals or rainfall
    for col in ['rainfall_7d', 'arrival_7d_mean']:
        if (df[col] < 0).any():
            print(f"FAILED: Negative values found in {col}")
        else:
            print(f"OK: No negative values in {col}")

    # Check temporal leakage
    # We shouldn't see future dates being populated early, but since it's a historical store, we just ensure 
    # date max doesn't exceed current time (unless data is from future, which it shouldn't be).
    if pd.to_datetime(df['date']).max() > pd.Timestamp.now():
        print("WARNING: Future dates found in feature store.")
    else:
        print("OK: No future leakage detected.")

if __name__ == '__main__':
    verify_features()
