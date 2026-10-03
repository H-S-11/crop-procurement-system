import pandas as pd
from sqlalchemy import create_engine
import os

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/data_provenance.csv')
    df.to_sql('data_provenance', engine, if_exists='append', index=False)
    print(f"Loaded {len(df)} provenance rows")

if __name__ == '__main__':
    load()
