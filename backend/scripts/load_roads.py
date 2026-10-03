import sqlite3
import os
from sqlalchemy import create_engine, text

def parse_gpkg_geom(blob):
    if not blob or blob[:2] != b'GP': return None
    flags = blob[3]
    env_indicator = (flags >> 1) & 7
    header_len = 8
    if env_indicator == 1: header_len += 32
    elif env_indicator in (2, 3): header_len += 48
    elif env_indicator == 4: header_len += 64
    wkb = blob[header_len:]
    return wkb

def load():
    db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db')
    engine = create_engine(db_url)
    
    gpkg_path = '../data/road_network/planet_78.80,9.85_79.58,11.20-geopackage/planet_78.80,9.85_79.58,11.20.gpkg'
    
    if not os.path.exists(gpkg_path):
        print(f"File {gpkg_path} not found")
        return
        
    conn_sl = sqlite3.connect(gpkg_path)
    cur = conn_sl.cursor()
    # Check if 'lines' table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lines'")
    if not cur.fetchone():
        print("Table 'lines' not found in geopackage")
        return
        
    cur.execute("SELECT osm_id, highway, geom FROM lines")
    rows = cur.fetchall()
    
    query = text('''
        INSERT INTO roads (id, road_class, source, geom) 
        VALUES (:id, :road_class, 'OSM', ST_SetSRID(ST_GeomFromWKB(:geom), 4326))
    ''')
    
    with engine.begin() as conn_pg:
        count = 0
        for row in rows:
            osm_id, highway, geom_blob = row
            wkb = parse_gpkg_geom(geom_blob) if geom_blob else None
            
            conn_pg.execute(query, {
                "id": str(osm_id),
                "road_class": highway,
                "geom": wkb
            })
            count += 1
            
    print(f"Loaded {count} roads")

if __name__ == '__main__':
    load()
