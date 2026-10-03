import pandas as pd
from sqlalchemy import create_engine
import os
import logging

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/B11_road_closure_events_Thanjavur.csv')
    if len(df) != 4984:
        logging.warning(f"Expected 4984 rows in B11, got {len(df)}")
    
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['geom'] = df.apply(lambda row: f"SRID=4326;POINT({row.longitude} {row.latitude})" if pd.notnull(row.longitude) else None, axis=1)
        out_df = df[['closure_id', 'road_id', 'date_start', 'date_end', 'closure_reason', 'geom']].rename(columns={'closure_id': 'id', 'closure_reason': 'reason'})
    else:
        out_df = df[['closure_id', 'road_id', 'date_start', 'date_end', 'closure_reason']].rename(columns={'closure_id': 'id', 'closure_reason': 'reason'})
    
    out_df.to_sql('road_closures', engine, if_exists='append', index=False)
    print(f"Loaded {len(out_df)} road closures")

if __name__ == '__main__':
    load()
