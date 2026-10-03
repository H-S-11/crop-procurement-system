import pandas as pd
from sqlalchemy import create_engine
import os
import logging
import uuid

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/B5_godown_mill_ledger_Thanjavur.csv')
    if len(df) != 2834:
        logging.warning(f"Expected 2834 rows in B5, got {len(df)}")
    
    out_df = df[['record_id', 'facility_id', 'date', 'closing_stock_mt', 'storage_capacity_mt']].rename(columns={'record_id': 'id', 'facility_id': 'godown_id', 'closing_stock_mt': 'occupancy_mt', 'storage_capacity_mt': 'capacity_mt'})
    out_df.to_sql('godown_ledger', engine, if_exists='append', index=False, chunksize=5000, method='multi')
    print(f"Loaded {len(out_df)} godown ledger rows")

if __name__ == '__main__':
    load()
