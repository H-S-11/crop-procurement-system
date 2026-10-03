import pandas as pd
from sqlalchemy import create_engine
import os
import glob

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    files = glob.glob('../data/flood/*.tif')
    data = []
    for f in files:
        data.append({
            'filename': os.path.basename(f),
            'filepath': os.path.abspath(f),
            'source': 'Sentinel-1',
            'date': None
        })
    df = pd.DataFrame(data)
    df.to_sql('sar_flood_rasters', engine, if_exists='append', index=False)
    print(f"Loaded {len(df)} sar flood rasters metadata")

if __name__ == '__main__':
    load()
