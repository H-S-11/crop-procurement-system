import pandas as pd
import numpy as np
import rasterio
from rasterio.warp import transform
import os

def generate_flood_features(engine=None):
    print("Loading DPC geometries...")
    csv_path = os.path.join(os.path.dirname(__file__), '../../data/B1_DPC_master_layer_Thanjavur.csv')
    dpcs = pd.read_csv(csv_path)
    
    if 'dpc_id' in dpcs.columns:
        dpcs = dpcs.rename(columns={'dpc_id': 'dpc_id'})
    
    if dpcs.empty:
        return pd.DataFrame(columns=['dpc_id', 'flood_exposure', 'flood_frequency'])

    raster_path = os.path.join(os.path.dirname(__file__), '../../data/flood/thanjavur_flood_extent_2025.tif')
    
    if not os.path.exists(raster_path):
        print("Warning: Flood extent mask not found, setting explicit unavailable values.")
        dpcs['flood_exposure'] = None
        dpcs['flood_frequency'] = None
        return dpcs[['dpc_id', 'flood_exposure', 'flood_frequency']]
    
    print("Calculating flood exposure from Sentinel-1 classification mask...")
    try:
        with rasterio.open(raster_path) as src:
            crs = src.crs
            xs, ys = transform('EPSG:4326', crs, dpcs['longitude'].tolist(), dpcs['latitude'].tolist())
            
            is_projected = crs.is_projected
            buffer_dist = 500 if is_projected else 0.005
            
            res_x, res_y = src.res
            radius_x = max(1, int(buffer_dist / res_x))
            radius_y = max(1, int(buffer_dist / res_y))
            
            exposures = []
            
            for x, y in zip(xs, ys):
                py, px = src.index(x, y)
                window = rasterio.windows.Window(
                    col_off=px - radius_x, 
                    row_off=py - radius_y, 
                    width=2 * radius_x + 1, 
                    height=2 * radius_y + 1
                )
                window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                
                if window.width > 0 and window.height > 0:
                    data = src.read(1, window=window)
                    if src.nodata is not None:
                        mask = (data != src.nodata)
                    else:
                        mask = np.ones_like(data, dtype=bool)
                        
                    valid_pixels = np.sum(mask)
                    if valid_pixels > 0:
                        flood_pixels = np.sum((data > 0) & mask)
                        exposures.append(flood_pixels / valid_pixels)
                    else:
                        exposures.append(0.0)
                else:
                    exposures.append(0.0)
                    
            dpcs['flood_exposure'] = exposures
            dpcs['flood_frequency'] = exposures
            
    except Exception as e:
        print(f"Error processing flood raster: {e}")
        dpcs['flood_exposure'] = None
        dpcs['flood_frequency'] = None
        
    return dpcs[['dpc_id', 'flood_exposure', 'flood_frequency']]
