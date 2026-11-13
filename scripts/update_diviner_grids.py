"""
Enhance Moon Diviner GCP grids using the standard 1-hour midday (11.5 - 12.5 h)
and 1-hour midnight (23.5 - 0.5 h) local solar time averaging (Williams et al. 2017).
"""
import os
import urllib.request
import numpy as np
import rasterio
from rasterio.transform import from_origin

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'moon', 'thermal')
GCP_URL = 'https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/global_cumul_avg_cyl_00n10n_002.tab'

def update_diviner_grids():
    day_tif = os.path.join(OUT_DIR, 'diviner_day.tif')
    night_tif = os.path.join(OUT_DIR, 'diviner_night.tif')
    
    day_sum = np.zeros((20, 720), dtype=np.float64)
    day_cnt = np.zeros((20, 720), dtype=np.int32)
    night_sum = np.zeros((20, 720), dtype=np.float64)
    night_cnt = np.zeros((20, 720), dtype=np.int32)
    
    print("Streaming GCP table with 1-hr diurnal bins...")
    req = urllib.request.Request(GCP_URL, headers={'User-Agent': 'TerraTwin/1.0'})
    with urllib.request.urlopen(req) as resp:
        for count, line in enumerate(resp):
            parts = line.decode('utf-8', errors='ignore').strip().split(',')
            if len(parts) < 11 or parts[0].strip() == 'clon':
                continue
            try:
                clon = float(parts[0].strip())
                clat = float(parts[1].strip())
                ltim = float(parts[2].strip())
                tbol = float(parts[10].strip())
            except ValueError:
                continue
            
            if tbol <= 0:
                continue
                
            row = int(np.floor((9.75 - clat) / 0.5 + 0.5))
            col = int(np.floor((clon - (-179.75)) / 0.5 + 0.5))
            if 0 <= row < 20 and 0 <= col < 720:
                if 11.5 <= ltim <= 12.5:
                    day_sum[row, col] += tbol
                    day_cnt[row, col] += 1
                elif ltim >= 23.5 or ltim <= 0.5:
                    night_sum[row, col] += tbol
                    night_cnt[row, col] += 1

    day_grid = np.where(day_cnt > 0, (day_sum / np.maximum(day_cnt, 1)).astype(np.float32), -9999.0)
    night_grid = np.where(night_cnt > 0, (night_sum / np.maximum(night_cnt, 1)).astype(np.float32), -9999.0)
    
    transform = from_origin(-180.0, 10.0, 0.5, 0.5)
    meta = {
        'driver': 'GTiff',
        'height': 20,
        'width': 720,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:4326',
        'transform': transform,
        'nodata': -9999.0,
        'compress': 'deflate'
    }
    
    with rasterio.open(day_tif, 'w', **meta) as dst:
        dst.write(day_grid, 1)
    with rasterio.open(night_tif, 'w', **meta) as dst:
        dst.write(night_grid, 1)
        
    print(f"Updated diviner_day.tif: valid = {np.sum(day_grid > 0)}/14400 ({np.sum(day_grid > 0)/14400*100:.1f}%)")
    print(f"Updated diviner_night.tif: valid = {np.sum(night_grid > 0)}/14400 ({np.sum(night_grid > 0)/14400*100:.1f}%)")

if __name__ == '__main__':
    update_diviner_grids()
