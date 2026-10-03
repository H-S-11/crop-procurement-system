import json
import os
from sqlalchemy import create_engine, text

def load():
    db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/paddy_db')
    engine = create_engine(db_url)
    
    with open('../data/boundaries/thanjavur_boundaries.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    print(f"Loading {len(features)} villages from GeoJSON...")
    
    query = text('''
        INSERT INTO villages (id, name, block, paddy_area_ha, expected_yield, geom) 
        VALUES (:id, :name, :block, :paddy_area_ha, :expected_yield, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
    ''')
    
    with engine.begin() as conn:
        count = 0
        for feat in features:
            props = feat['properties']
            geom = json.dumps(feat['geometry'])
            
            # Assuming 'id', 'name', 'block', 'paddy_area_ha', 'expected_yield' are in properties
            # Adjust mapping if property names differ in actual file
            id_val = str(props.get('id', count))
            name = props.get('name', 'Unknown')
            block = props.get('block', '')
            paddy_area = float(props.get('paddy_area_ha', 0.0))
            expected_yield = float(props.get('expected_yield', 0.0))
            
            conn.execute(query, {
                "id": id_val,
                "name": name,
                "block": block,
                "paddy_area_ha": paddy_area,
                "expected_yield": expected_yield,
                "geom": geom
            })
            count += 1
            
    print(f"Loaded {count} villages")

if __name__ == '__main__':
    load()
