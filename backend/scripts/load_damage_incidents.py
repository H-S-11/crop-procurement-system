import pandas as pd
from sqlalchemy import create_engine
import os
import logging

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/B10_damage_incident_register_Thanjavur.csv')
    if len(df) != 170:
        logging.warning(f"Expected 170 rows in B10, got {len(df)}")
    
    out_df = df[['incident_id', 'dpc_id', 'date_reported', 'estimated_damage_mt', 'primary_cause', 'data_source_flag']].rename(columns={'incident_id': 'id', 'date_reported': 'date', 'estimated_damage_mt': 'tonnage_damaged', 'primary_cause': 'cause', 'data_source_flag': 'source'})
    # Map mixed observed/synthetic
    out_df['source'] = out_df['source'].apply(lambda x: 'synthetic' if 'SYNTHETIC' in str(x).upper() else 'observed')
    out_df.to_sql('damage_incidents', engine, if_exists='append', index=False)
    print(f"Loaded {len(out_df)} damage incidents")

if __name__ == '__main__':
    load()
