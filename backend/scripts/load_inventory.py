import pandas as pd
from sqlalchemy import create_engine
import os
import logging

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/B7_consumables_inventory_Thanjavur.csv')
    if len(df) != 61426:
        logging.warning(f"Expected 61426 rows in B7, got {len(df)}")
    out_df = df[['dpc_id', 'date', 'gunnies_available_nos', 'tarpaulins_available_nos']].rename(columns={'gunnies_available_nos': 'gunny_bags_available', 'tarpaulins_available_nos': 'tarpaulin_available'})
    out_df.to_sql('inventory_gunny_tarpaulin', engine, if_exists='append', index=False, chunksize=5000, method='multi')
    print(f"Loaded {len(out_df)} inventory rows")

if __name__ == '__main__':
    load()
