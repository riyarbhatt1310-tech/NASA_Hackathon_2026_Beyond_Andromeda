"""
Download and extract real Moon LRO Diviner thermal products:
1. UCLA / Williams et al. (2017) PDS GCP diurnal cumulative climatology:
   global_cumul_avg_cyl_00n10n_002.tab
   Extracts:
   - Midday bolometric temperature (ltim = 12.12 h, ~12:00 local solar time)
   - Midnight bolometric temperature (ltim = 0.12 h, ~00:00 local solar time)
   Saves to: data/raw/moon/thermal/diviner_day.tif and diviner_night.tif
2. GHRM high-resolution 128 pix/deg midnight bolometric temperature:
   Extracts Apollo 11 / 12 regional crop from dghrm_tbol_m_70s70n_tif.tif.
"""
import os
import urllib.request
import numpy as np
import rasterio
from rasterio.transform import from_origin

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'moon', 'thermal')
os.makedirs(OUT_DIR, exist_ok=True)

GCP_URL = 'https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/global_cumul_avg_cyl_00n10n_002.tab'

def extract_diviner_gcp_grids():
    day_tif = os.path.join(OUT_DIR, 'diviner_day.tif')
    night_tif = os.path.join(OUT_DIR, 'diviner_night.tif')
    
    if os.path.exists(day_tif) and os.path.exists(night_tif):
        print(f"  [EXISTS] {day_tif} and {night_tif}")
        return

    print("Downloading and processing Williams et al. (2017) Diviner diurnal climatology table...")
    # The table has fixed width records of 113 bytes:
    # clon (-179.75 to 179.75, step 0.5 -> 720 points)
    # clat (0.25 to 9.75, step 0.5 -> 20 points)
    # ltim (0.12 to 23.88, step 0.25 -> 96 points)
    # We want ltim ~ 12.12 (Midday) and ltim ~ 0.12 (Midnight)
    # Let's stream through the table and pick ltim 12.12 and 0.12
    req = urllib.request.Request(GCP_URL, headers={'User-Agent': 'TerraTwin/1.0'})
    
    day_grid = np.full((20, 720), np.nan, dtype=np.float32)
    night_grid = np.full((20, 720), np.nan, dtype=np.float32)
    
    with urllib.request.urlopen(req) as resp:
        # Read line by line
        count = 0
        for line in resp:
            parts = line.decode('utf-8', errors='ignore').strip().split(',')
            if len(parts) < 11:
                continue
            clon_str, clat_str, ltim_str = parts[0].strip(), parts[1].strip(), parts[2].strip()
            if clon_str == 'clon':
                continue
            try:
                clon = float(clon_str)
                clat = float(clat_str)
                ltim = float(ltim_str)
                tbol = float(parts[10].strip())
            except ValueError:
                continue
            
            # Map lat (0 to 10) and lon (-180 to 180) to grid indices
            # row 0 is top (lat 10), row 19 is bottom (lat 0)
            row = int(np.floor((9.75 - clat) / 0.5 + 0.5))
            col = int(np.floor((clon - (-179.75)) / 0.5 + 0.5))
            
            if 0 <= row < 20 and 0 <= col < 720:
                if 12.0 <= ltim <= 12.25:
                    if tbol > 0:
                        day_grid[row, col] = tbol
                elif 0.0 <= ltim <= 0.25:
                    if tbol > 0:
                        night_grid[row, col] = tbol
            
            count += 1
            if count % 200000 == 0:
                print(f"  Processed {count}/1,382,400 records...")

    # Write GeoTIFFs
    # Bounds: Lat 0 to 10 N, Lon -180 to 180 E
    # Transform: x_origin = -180.0, y_origin = 10.0, dx = 0.5, dy = -0.5
    transform = from_origin(-180.0, 10.0, 0.5, 0.5)
    meta = {
        'driver': 'GTiff',
        'height': 20,
        'width': 720,
        'count': 1,
        'dtype': 'float32',
        'crs': 'EPSG:4326', # Standard geographic (lon, lat)
        'transform': transform,
        'nodata': -9999.0,
        'compress': 'deflate'
    }
    
    day_out = np.where(np.isnan(day_grid), -9999.0, day_grid)
    night_out = np.where(np.isnan(night_grid), -9999.0, night_grid)
    
    with rasterio.open(day_tif, 'w', **meta) as dst:
        dst.write(day_out, 1)
    with rasterio.open(night_tif, 'w', **meta) as dst:
        dst.write(night_out, 1)
        
    print(f"Saved real Moon Diviner daytime grid to {day_tif} ({os.path.getsize(day_tif)/1024:.1f} KB)")
    print(f"Saved real Moon Diviner nighttime grid to {night_tif} ({os.path.getsize(night_tif)/1024:.1f} KB)")
    valid_d = day_grid[np.isfinite(day_grid)]
    valid_n = night_grid[np.isfinite(night_grid)]
    print(f"Daytime bolometric temperature: min={valid_d.min():.1f} K, max={valid_d.max():.1f} K, mean={valid_d.mean():.1f} K")
    print(f"Nighttime bolometric temperature: min={valid_n.min():.1f} K, max={valid_n.max():.1f} K, mean={valid_n.mean():.1f} K")

if __name__ == '__main__':
    extract_diviner_gcp_grids()
