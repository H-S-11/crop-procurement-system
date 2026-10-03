import pandas as pd
from sqlalchemy import create_engine
import os

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/rainfall_observations.csv')
    df['geom'] = df.apply(lambda row: f"SRID=4326;POINT({row.longitude} {row.latitude})", axis=1)
    out_df = df[['station_id', 'date', 'rainfall_mm', 'geom']]
    out_df.to_sql('rainfall_observations', engine, if_exists='append', index=False)
    print(f"Loaded {len(out_df)} rainfall observations")

if __name__ == '__main__':
    load()
