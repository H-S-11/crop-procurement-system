from sqlalchemy import create_engine, text
import os

def verify():
    engine = create_engine(os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db'))
    tables = {
        'dpcs': 483,
        'arrivals': 61426,
        'godown_ledger': 2834,
        'inventory_gunny_tarpaulin': 61426,
        'road_closures': 4984,
        'damage_incidents': 170,
        'rainfall_observations': None,
        'sar_flood_rasters': None,
        'data_provenance': 11
    }
    with engine.connect() as conn:
        for t, expected in tables.items():
            res = conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            if expected is not None and res != expected:
                print(f"MISMATCH in {t}: expected {expected}, got {res}")
            else:
                print(f"Table {t}: {res} rows (OK)")

if __name__ == '__main__':
    verify()
