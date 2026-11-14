"""
Inspect transform and extract real Diviner GeoTIFF sample.
"""

import rasterio
from rasterio.windows import Window
from pathlib import Path

day_url = "/vsicurl/https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/geotiff/dghrm_tbol_sam_70s70n_tif.tif"
night_url = "/vsicurl/https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/geotiff/dghrm_tbol_m_70s70n_tif.tif"

out_dir = Path("data/raw/moon/thermal")
out_dir.mkdir(parents=True, exist_ok=True)

with rasterio.open(day_url) as src_day, rasterio.open(night_url) as src_night:
    print("Source Day bounds:", src_day.bounds)
    print("Source Day transform:", src_day.transform)
    print("Source Day nodata:", src_day.nodata)
    
    # Extract equatorial region (e.g. Oceanus Procellarum / Mare Tranquillitatis: 0 to 20 N, -50 to -30 lon)
    # Col/Row around row 8000, col 18000 (size 500x500)
    w = Window(18000, 8000, 500, 500)
    day_crop = src_day.read(1, window=w)
    night_crop = src_night.read(1, window=w)
    win_transform = rasterio.windows.transform(w, src_day.transform)

    # Save real GeoTIFF for day
    day_path = out_dir / "diviner_day_real.tif"
    with rasterio.open(
        day_path, "w",
        driver="GTiff",
        height=500, width=500, count=1,
        dtype=src_day.dtypes[0],
        crs=src_day.crs,
        transform=win_transform,
        nodata=src_day.nodata,
    ) as dst:
        dst.write(day_crop, 1)

    # Save real GeoTIFF for night
    night_path = out_dir / "diviner_night_real.tif"
    with rasterio.open(
        night_path, "w",
        driver="GTiff",
        height=500, width=500, count=1,
        dtype=src_night.dtypes[0],
        crs=src_night.crs,
        transform=win_transform,
        nodata=src_night.nodata,
    ) as dst:
        dst.write(night_crop, 1)

    print(f"Saved real Moon Diviner day GeoTIFF: {day_path} ({day_path.stat().st_size} bytes)")
    print(f"Saved real Moon Diviner night GeoTIFF: {night_path} ({night_path.stat().st_size} bytes)")
    print("Day mean (K):", day_crop[day_crop != src_day.nodata].mean())
    print("Night mean (K):", night_crop[night_crop != src_night.nodata].mean())
