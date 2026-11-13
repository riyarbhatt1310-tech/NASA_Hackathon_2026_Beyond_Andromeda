import rasterio
from rasterio.windows import Window
import rasterio.windows
import numpy as np
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'mars', 'thermal')
os.makedirs(OUT_DIR, exist_ok=True)
out_tif = os.path.join(OUT_DIR, 'themis_ti_jezero_100m.tif')

url = 'https://asc-astropedia.s3.us-west-2.amazonaws.com/Mars/Odyssey/THEMIS-Global-Thermal-Inertia-Mosaic/Quantitative-32-Bit/ancillary/THEMIS_TI_Mosaic_Quant_00N060E_100mpp.tif'
vsi = '/vsicurl/' + url

print("Extracting real THEMIS 100m thermal inertia over Jezero Crater...")
with rasterio.open(vsi) as src:
    R = 3396190.0
    x = R * np.radians(77.58)
    y = R * np.radians(18.38)
    row, col = src.index(x, y)
    
    # 500x500 window = 50 km x 50 km covering Jezero and surrounding delta deposits
    w = Window(col - 250, row - 250, 500, 500)
    data = src.read(1, window=w)
    win_transform = rasterio.windows.transform(w, src.transform)
    
    meta = src.meta.copy()
    meta.update({
        'driver': 'GTiff',
        'height': 500,
        'width': 500,
        'transform': win_transform,
        'compress': 'lzw',
        'nodata': -9999.0
    })
    
    with rasterio.open(out_tif, 'w', **meta) as dst:
        dst.write(data, 1)
    
    print(f"Saved real THEMIS Jezero crop to {out_tif} ({os.path.getsize(out_tif)/(1024*1024):.2f} MB)")
    valid = data[(data > 0) & (data < 2000)]
    print(f"Valid pixels: {valid.size}/{data.size} ({valid.size/data.size*100:.1f}%)")
    print(f"Thermal Inertia: min={valid.min():.1f}, max={valid.max():.1f}, mean={valid.mean():.1f} tiu")
