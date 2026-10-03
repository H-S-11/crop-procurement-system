import pandas as pd
import os

def generate_spatial_features(engine=None):
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/B1_DPC_master_layer_Thanjavur.csv')
    df = pd.read_csv(csv_path)
    # Rename columns to match expected output
    df = df.rename(columns={
        'dpc_id': 'dpc_id',
        'dpc_name': 'name',
        'design_capacity_mt': 'capacity',
        'elevation_m_msl': 'elevation',
        'block_panchayat_union': 'block'
    })
    # We might not have village, mock it
    df['village'] = df['block']
    return df[['dpc_id', 'name', 'capacity', 'elevation', 'longitude', 'latitude', 'block', 'village']]
