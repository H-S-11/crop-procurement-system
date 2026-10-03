import pandas as pd
from sqlalchemy import create_engine
import os
import logging

def load():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    df = pd.read_csv('../data/B1_DPC_master_layer_Thanjavur.csv')
    if len(df) != 483:
        logging.warning(f"Expected 483 rows in B1, got {len(df)}")
    
    df['geom'] = df.apply(lambda row: f"SRID=4326;POINT({row.longitude} {row.latitude})", axis=1)
    
    out_df = df[['dpc_id', 'dpc_name', 'geom', 'design_capacity_mt', 'block_panchayat_union', 'elevation_m_msl', 'waterlogging_risk_class', 'open_yard_area_cents']].copy()
    out_df = out_df.rename(columns={'dpc_id': 'id', 'dpc_name': 'name', 'design_capacity_mt': 'capacity_mt', 'block_panchayat_union': 'block', 'elevation_m_msl': 'elevation_m', 'waterlogging_risk_class': 'flood_risk_class', 'open_yard_area_cents': 'design_area_cents'})
    out_df['village_id'] = None
    out_df['road_distance_m'] = None
    
    out_df.to_sql('dpcs', engine, if_exists='append', index=False)
    print(f"Loaded {len(out_df)} dpcs")

if __name__ == '__main__':
    load()
