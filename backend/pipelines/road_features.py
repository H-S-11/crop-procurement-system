import os
import json
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

def generate_road_features(engine=None):
    print("Calculating real nearest road distances from OSM road network...")
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/B1_DPC_master_layer_Thanjavur.csv')
    df = pd.read_csv(csv_path)
    
    roads_path = os.path.join(os.path.dirname(__file__), '../../data/boundaries/thanjavur_roads.geojson')
    
    if not os.path.exists(roads_path):
        print("Road network geojson not found, using conservative fallback distances.")
        df['nearest_road_dist'] = 450.0
        df['major_road_dist'] = 1500.0
        df['road_density'] = 4.2
        return df[['dpc_id', 'nearest_road_dist', 'major_road_dist', 'road_density']]
        
    with open(roads_path, 'r', encoding='utf-8') as f:
        roads_data = json.load(f)
        
    # Extract road vertices
    road_pts = []
    major_pts = []
    
    for feat in roads_data.get('features', []):
        highway = feat.get('properties', {}).get('highway', '')
        coords = feat.get('geometry', {}).get('coordinates', [])
        for c in coords:
            road_pts.append(c)
            if highway in ('trunk', 'primary', 'secondary'):
                major_pts.append(c)
                
    if not road_pts:
        road_pts = [[79.18, 10.75]]
    if not major_pts:
        major_pts = road_pts
        
    road_arr = np.array(road_pts)
    major_arr = np.array(major_pts)
    
    # Project to meters approx for Thanjavur (~10.75 deg Lat)
    mean_lat = 10.75
    cos_lat = np.cos(np.radians(mean_lat))
    scale = np.array([111320 * cos_lat, 110540])
    
    road_meters = road_arr * scale
    major_meters = major_arr * scale
    
    tree_all = cKDTree(road_meters)
    tree_major = cKDTree(major_meters)
    
    dpc_coords = df[['longitude', 'latitude']].values * scale
    
    dist_all, _ = tree_all.query(dpc_coords)
    dist_major, _ = tree_major.query(dpc_coords)
    
    df['nearest_road_dist'] = np.round(dist_all, 1)
    df['major_road_dist'] = np.round(dist_major, 1)
    # Estimated local road density (number of road nodes within 3 km)
    counts = tree_all.query_ball_point(dpc_coords, r=3000, return_length=True)
    df['road_density'] = np.round(np.array(counts) / (np.pi * 3.0**2), 2)
    
    print(f"Computed road features for {len(df)} DPCs. Mean dist to road: {df['nearest_road_dist'].mean():.1f}m, major: {df['major_road_dist'].mean():.1f}m")
    return df[['dpc_id', 'nearest_road_dist', 'major_road_dist', 'road_density']]
