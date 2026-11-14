"""
Download real NASA MODIS Level-3 (MYD11A1.061) Cloud-Optimized GeoTIFFs from Planetary Computer.
Region: Mojave Desert / Death Valley terrestrial analog (Tile h08v05, date 2023-07-16 / DOY 197).
"""
import os
import urllib.request
import urllib.parse
import json

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'earth', 'thermal')
os.makedirs(OUT_DIR, exist_ok=True)

ASSETS = {
    'modis_lst_day.tif': 'https://modiseuwest.blob.core.windows.net/modis-061-cogs/MYD11A1/08/05/2023197/MYD11A1.A2023197.h08v05.061.2023213033900_LST_Day_1km.tif',
    'modis_lst_night.tif': 'https://modiseuwest.blob.core.windows.net/modis-061-cogs/MYD11A1/08/05/2023197/MYD11A1.A2023197.h08v05.061.2023213033900_LST_Night_1km.tif',
    'modis_qc_day.tif': 'https://modiseuwest.blob.core.windows.net/modis-061-cogs/MYD11A1/08/05/2023197/MYD11A1.A2023197.h08v05.061.2023213033900_QC_Day.tif',
    'modis_qc_night.tif': 'https://modiseuwest.blob.core.windows.net/modis-061-cogs/MYD11A1/08/05/2023197/MYD11A1.A2023197.h08v05.061.2023213033900_QC_Night.tif',
}

def sign_url(raw_url: str) -> str:
    sign_api = f'https://planetarycomputer.microsoft.com/api/sas/v1/sign?href={urllib.parse.quote(raw_url)}'
    req = urllib.request.Request(sign_api, headers={'User-Agent': 'TerraTwin/1.0'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))['href']

def main():
    print(f"Downloading real Earth MODIS products to {OUT_DIR}...")
    for filename, raw_url in ASSETS.items():
        out_path = os.path.join(OUT_DIR, filename)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
            print(f"  [ALREADY EXISTS] {filename} ({os.path.getsize(out_path)/(1024*1024):.2f} MB)")
            continue
        print(f"  Signing URL for {filename}...")
        signed = sign_url(raw_url)
        print(f"  Downloading {filename}...")
        urllib.request.urlretrieve(signed, out_path)
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        print(f"  -> Saved {filename} ({size_mb:.2f} MB)")

if __name__ == '__main__':
    main()
