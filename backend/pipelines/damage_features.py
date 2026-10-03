import pandas as pd
import os

def generate_damage_features(engine=None):
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/B10_damage_incident_register_Thanjavur.csv')
    df = pd.read_csv(csv_path)
    
    # Filter for DPCs
    df = df[df['entity_type'] == 'DPC'].copy()
    
    if df.empty:
        return pd.DataFrame(columns=['dpc_id', 'damage_incidence_rate', 'historical_damage_events'])
        
    df['start_date'] = pd.to_datetime(df['start_date'])
    
    # Calculate per-DPC damage incidence
    incidents = df.groupby('entity_id').size().reset_index(name='historical_damage_events')
    incidents = incidents.rename(columns={'entity_id': 'dpc_id'})
    
    max_events = incidents['historical_damage_events'].max()
    incidents['damage_incidence_rate'] = incidents['historical_damage_events'] / (max_events if max_events > 0 else 1)
    
    return incidents[['dpc_id', 'damage_incidence_rate', 'historical_damage_events']]
