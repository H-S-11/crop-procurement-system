import pandas as pd
import os

def generate_access_features(engine=None):
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/B11_road_closure_events_Thanjavur.csv')
    df = pd.read_csv(csv_path)
    
    if df.empty:
        return pd.DataFrame(columns=['dpc_id', 'date', 'access_disruption'])
        
    df['date'] = pd.to_datetime(df['date'])
    
    # B11 represents road closure events. We will mark these dates as access_disruption = 1 for the given DPC
    df['access_disruption'] = 1.0
    
    # We could also use closure_severity_score_0_1, let's just use it directly or default to 1.0
    if 'closure_severity_score_0_1' in df.columns:
        df['access_disruption'] = df['closure_severity_score_0_1'].fillna(1.0)
        
    # Group by DPC and Date in case of multiple events per day
    df_grouped = df.groupby(['dpc_id', 'date'])['access_disruption'].max().reset_index()
    
    return df_grouped[['dpc_id', 'date', 'access_disruption']]
