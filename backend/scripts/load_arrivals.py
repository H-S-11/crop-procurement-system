import pandas as pd
from sqlalchemy import create_engine
import os
import logging

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/B2_daily_arrivals_Thanjavur.csv')
    if len(df) != 61426:
        logging.warning(f"Expected 61426 rows in B2, got {len(df)}")
    out_df = df[['dpc_id', 'date', 'gross_presented_mt', 'mean_moisture_pct']].rename(columns={'gross_presented_mt': 'mt_arrived', 'mean_moisture_pct': 'moisture_pct'})
    out_df.to_sql('arrivals', engine, if_exists='append', index=False, chunksize=5000, method='multi')
    print(f"Loaded {len(out_df)} arrivals")

if __name__ == '__main__':
    load()
