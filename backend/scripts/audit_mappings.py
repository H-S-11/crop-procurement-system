import pandas as pd
from database import SessionLocal
from models import DPC

db = SessionLocal()
dpc_ids = {d.id for d in db.query(DPC.id).all()}

# B10 check
b10 = pd.read_csv('../data/B10_damage_incident_register_Thanjavur.csv')
b10_cols = b10.columns.tolist()
b10_dpc_col = 'entity_id' if 'entity_id' in b10_cols else None
b10_matched = b10[b10_dpc_col].isin(dpc_ids).sum() if b10_dpc_col else 0
b10_unmatched = len(b10) - b10_matched

# B11 check
b11 = pd.read_csv('../data/B11_road_closure_events_Thanjavur.csv')
b11_cols = b11.columns.tolist()
b11_dpc_col = 'dpc_id' if 'dpc_id' in b11_cols else None
b11_matched = b11[b11_dpc_col].isin(dpc_ids).sum() if b11_dpc_col else 0
b11_unmatched = len(b11) - b11_matched

print(f"B10 cols: {b10_cols}")
print(f"B10 Matched: {b10_matched}, Unmatched: {b10_unmatched}")
print(f"B11 cols: {b11_cols}")
print(f"B11 Matched: {b11_matched}, Unmatched: {b11_unmatched}")
