import pandas as pd
import os
import numpy as np

def generate_rainfall_features(engine=None):
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/rainfall_observations.csv')
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Mocking DPC spatial join by just assigning rainfall equally or mapping blindly
    dpc_csv = os.path.join(os.path.dirname(__file__), '../../data/B1_DPC_master_layer_Thanjavur.csv')
    dpcs = pd.read_csv(dpc_csv)
    
    # Get unique stations
    stations = df[['station_id', 'latitude', 'longitude']].drop_duplicates()
    
    # Calculate nearest station for each DPC
    dpc_stations = []
    for _, dpc in dpcs.iterrows():
        # Simple euclidean distance for assignment
        dist = (stations['latitude'] - dpc['latitude'])**2 + (stations['longitude'] - dpc['longitude'])**2
        nearest = stations.loc[dist.idxmin(), 'station_id']
        dpc_stations.append({'dpc_id': dpc['dpc_id'], 'station_id': nearest})
        
    dpc_station_map = pd.DataFrame(dpc_stations)
    
    # Sort and compute rolling features per station
    df = df.sort_values(['station_id', 'date'])
    df['rainfall_1d'] = df['rainfall_mm']
    df['rainfall_3d'] = df.groupby('station_id')['rainfall_mm'].rolling(3, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainfall_7d'] = df.groupby('station_id')['rainfall_mm'].rolling(7, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainfall_14d'] = df.groupby('station_id')['rainfall_mm'].rolling(14, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainfall_30d'] = df.groupby('station_id')['rainfall_mm'].rolling(30, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainy_days_7d'] = df.groupby('station_id')['rainfall_mm'].apply(lambda x: (x > 0).rolling(7, min_periods=1).sum()).reset_index(level=0, drop=True)
    
    # Map back to DPCs
    result = dpc_station_map.merge(df, on='station_id', how='left')
    
    return result[['dpc_id', 'date', 'rainfall_1d', 'rainfall_3d', 'rainfall_7d', 'rainfall_14d', 'rainfall_30d', 'rainy_days_7d']]
