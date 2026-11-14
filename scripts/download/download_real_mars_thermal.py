"""
Download real Mars thermal datasets:
1. MGS TES Global Thermal Inertia (Putzig et al. 2007, NASA PDS Geosciences)
   - global_ti_day_2007.img (51.84 MB) + label
   - global_ti_night_2007.img (51.84 MB) + label
   - global_ti_msk_night_2007.img (25.92 MB) + label
2. Mars THEMIS 100m Quantitative Thermal Inertia:
   - Extract a real 100m resolution GeoTIFF crop over Jezero Crater (18.38 N, 77.58 E)
     from the official USGS Astropedia 32-bit mosaic.
"""
import os
import urllib.request
import struct
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'mars', 'thermal')
os.makedirs(OUT_DIR, exist_ok=True)

TES_FILES = {
    'global_ti_day_2007.lbl': 'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_day_2007.lbl',
    'global_ti_day_2007.img': 'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_day_2007.img',
    'global_ti_night_2007.lbl': 'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_night_2007.lbl',
    'global_ti_night_2007.img': 'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_night_2007.img',
    'global_ti_msk_night_2007.lbl': 'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_msk_night_2007.lbl',
    'global_ti_msk_night_2007.img': 'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_msk_night_2007.img',
}

def download_tes_files():
    print("Downloading MGS TES thermal inertia datasets from PDS Geosciences...")
    for fname, url in TES_FILES.items():
        dst = os.path.join(OUT_DIR, fname)
        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
            print(f"  [EXISTS] {fname} ({os.path.getsize(dst)/(1024*1024):.2f} MB)")
            continue
        print(f"  Downloading {fname} from {url}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
        with urllib.request.urlopen(req) as resp, open(dst, 'wb') as f:
            while chunk := resp.read(1024 * 1024):
                f.write(chunk)
        print(f"  -> Saved {fname} ({os.path.getsize(dst)/(1024*1024):.2f} MB)")

def extract_themis_jezero_crop():
    """
    Extracts a real scientific crop around Jezero Crater (18.38 N, 77.58 E) from
    the USGS Astropedia THEMIS 32-bit quantitative thermal inertia mosaic.
    Tile: THEMIS_TI_Mosaic_Quant_30N060E_100mpp.tif
    Extent of 30N060E tile: Lat 0 to 30 N, Lon 60 to 120 E.
    Resolution: 100 m/pixel (~592.74 pixels/degree).
    """
    out_tif = os.path.join(OUT_DIR, 'themis_ti_jezero_100m.tif')
    if os.path.exists(out_tif) and os.path.getsize(out_tif) > 500000:
        print(f"  [EXISTS] themis_ti_jezero_100m.tif ({os.path.getsize(out_tif)/(1024*1024):.2f} MB)")
        return

    print("Extracting real THEMIS 100m thermal inertia crop over Jezero Crater via HTTP range...")
    # The TIFF on S3 is uncompressed strip TIFF or tiled TIFF
    # Let's inspect the TIFF header from S3
    s3_url = 'https://asc-astropedia.s3.us-west-2.amazonaws.com/Mars/Odyssey/THEMIS-Global-Thermal-Inertia-Mosaic/Quantitative-32-Bit/ancillary/THEMIS_TI_Mosaic_Quant_30N060E_100mpp.tif'
    
    # We can use rasterio with vsicurl to read a focused 500x500 window (~50 km x 50 km)
    vsi_url = f'/vsicurl/{s3_url}'
    try:
        with rasterio.open(vsi_url) as src:
            print(f"  Opened remote THEMIS: shape={src.shape}, bounds={src.bounds}, crs={src.crs}")
            # Jezero: Lat 18.38, Lon 77.58. In Equirectangular (lon, lat)
            # Transform Jezero coord to pixel
            row, col = src.index(77.58, 18.38)
            print(f"  Jezero pixel index: row={row}, col={col}")
            from rasterio.windows import Window
            w = Window(col - 250, row - 250, 500, 500)
            data = src.read(1, window=w)
            win_transform = rasterio.windows.transform(w, src.transform)
            
            # Write out local GeoTIFF
            meta = src.meta.copy()
            meta.update({
                'height': 500,
                'width': 500,
                'transform': win_transform,
                'compress': 'deflate'
            })
            with rasterio.open(out_tif, 'w', **meta) as dst:
                dst.write(data, 1)
            print(f"  -> Saved real THEMIS Jezero crop ({os.path.getsize(out_tif)/(1024*1024):.2f} MB)")
            print(f"  TI range: min={data[data > 0].min():.1f}, max={data[data > 0].max():.1f}, mean={data[data > 0].mean():.1f} tiu")
    except Exception as e:
        print(f"  Remote THEMIS extraction error: {e}")

if __name__ == '__main__':
    download_tes_files()
    extract_themis_jezero_crop()
