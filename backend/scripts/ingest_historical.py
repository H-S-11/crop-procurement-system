import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pandas as pd
from datetime import datetime
from sqlalchemy.sql import text
from database import engine, SessionLocal
from models import Base, DamageIncident, RoadClosure, DPC

# Base.metadata.create_all(bind=engine)

def create_tables_if_not_exist(db):
    db.execute(text("""
    CREATE TABLE IF NOT EXISTS damage_incidents (
        id VARCHAR PRIMARY KEY,
        dpc_id VARCHAR,
        date DATE,
        tonnage_damaged FLOAT,
        cause VARCHAR,
        source VARCHAR,
        FOREIGN KEY(dpc_id) REFERENCES dpcs(id)
    )
    """))
    db.execute(text("""
    CREATE TABLE IF NOT EXISTS road_closures (
        id VARCHAR PRIMARY KEY,
        road_id VARCHAR,
        dpc_id VARCHAR,
        date_start DATE,
        date_end DATE,
        reason VARCHAR,
        geom GEOMETRY,
        FOREIGN KEY(road_id) REFERENCES roads(id),
        FOREIGN KEY(dpc_id) REFERENCES dpcs(id)
    )
    """))
    db.commit()

def ingest_data():
    db = SessionLocal()
    create_tables_if_not_exist(db)
    
    # Load DPC IDs for validation
    dpc_ids = {d.id for d in db.query(DPC.id).all()}
    
    # 1. B10 Damage Incidents
    print("Ingesting B10...")
    b10_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'B10_damage_incident_register_Thanjavur.csv')
    if os.path.exists(b10_path):
        b10_df = pd.read_csv(b10_path)
        existing_b10 = {r[0] for r in db.execute(text("SELECT id FROM damage_incidents")).fetchall()}
        b10_usable = 0
        for _, row in b10_df.iterrows():
            dpc_id = row['entity_id'] if row['entity_id'] in dpc_ids else None
            if row['incident_id'] in existing_b10:
                continue
                
            # Use raw SQL to insert B10 to bypass any ORM/geoalchemy issues
            db.execute(text("""
                INSERT INTO damage_incidents (id, dpc_id, date, tonnage_damaged, cause, source)
                VALUES (:id, :dpc_id, :date, :tonnage_damaged, :cause, :source)
            """), {
                "id": row['incident_id'],
                "dpc_id": dpc_id,
                "date": datetime.strptime(row['start_date'], '%Y-%m-%d').date() if pd.notna(row['start_date']) else None,
                "tonnage_damaged": row['loss_estimate_mt'],
                "cause": row['trigger'],
                "source": row['source']
            })
            b10_usable += 1
        db.commit()
        print(f"B10: Loaded {b10_usable} rows (Total: {len(b10_df)})")
    else:
        print("B10 source file not found")
        
    # 2. B11 Road Closures
    print("Ingesting B11...")
    b11_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'B11_road_closure_events_Thanjavur.csv')
    if os.path.exists(b11_path):
        b11_df = pd.read_csv(b11_path)
        # Get existing IDs to avoid AsEWKB error
        existing_b11 = {r[0] for r in db.execute(text("SELECT id FROM road_closures")).fetchall()}
        
        b11_usable = 0
        for _, row in b11_df.iterrows():
            dpc_id = row['dpc_id'] if row['dpc_id'] in dpc_ids else None
            if row['event_id'] in existing_b11:
                continue
            
            db.execute(text("""
                INSERT INTO road_closures (id, dpc_id, date_start, reason)
                VALUES (:id, :dpc_id, :date_start, :reason)
            """), {
                "id": row['event_id'],
                "dpc_id": dpc_id,
                "date_start": datetime.strptime(row['date'], '%Y-%m-%d').date() if pd.notna(row['date']) else None,
                "reason": row['closure_type']
            })
            b11_usable += 1
        db.commit()
        print(f"B11: Loaded {b11_usable} rows (Total: {len(b11_df)})")
    else:
        print("B11 source file not found")
            
    db.close()

if __name__ == "__main__":
    ingest_data()
