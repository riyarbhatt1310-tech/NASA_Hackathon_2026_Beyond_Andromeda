import os
import urllib.request
import json
import zipfile

BASE_DIR = r"C:\Users\maitr\.gemini\antigravity\scratch\terratwin"

def download_file(url, target_path):
    print(f"Downloading {url} -> {target_path}...")
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"  Already exists ({os.path.getsize(target_path)} bytes). Skipping.")
        return
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp, open(target_path, 'wb') as out:
        data = resp.read()
        out.write(data)
    print(f"  Downloaded {len(data)} bytes.")

# 1. Mars Odyssey GRS
mars_vol_dir = os.path.join(BASE_DIR, "data", "raw", "mars", "volatiles")
download_file(
    "https://pds-geosciences.wustl.edu/ody/ody-m-grs-5-elements-v1/odgm_xxxx/data/smoothed/h2o_sr_5x5.tab",
    os.path.join(mars_vol_dir, "h2o_sr_5x5.tab")
)
download_file(
    "https://pds-geosciences.wustl.edu/ody/ody-m-grs-5-elements-v1/odgm_xxxx/data/smoothed/h2o_sr_5x5.lbl",
    os.path.join(mars_vol_dir, "h2o_sr_5x5.lbl")
)

# 2. Moon LP-NS
moon_vol_dir = os.path.join(BASE_DIR, "data", "raw", "moon", "volatiles")
download_file(
    "https://pds-geosciences.wustl.edu/missions/lunarp/reduced/hydrogenlow.txt",
    os.path.join(moon_vol_dir, "hydrogenlow.txt")
)

# 3. Earth Glaciers (RGI Alaska regional test fixture)
earth_vol_dir = os.path.join(BASE_DIR, "data", "raw", "earth", "volatiles")
rgi_zip = os.path.join(earth_vol_dir, "01_rgi60_Alaska.zip")
download_file(
    "https://www.glims.org/RGI/rgi60_files/01_rgi60_Alaska.zip",
    rgi_zip
)
# Unzip RGI Alaska if needed
rgi_extract = os.path.join(earth_vol_dir, "rgi60_alaska")
if os.path.exists(rgi_zip) and not os.path.exists(rgi_extract):
    try:
        with zipfile.ZipFile(rgi_zip, 'r') as z:
            z.extractall(rgi_extract)
        print("  Extracted RGI Alaska shapefile.")
    except Exception as e:
        print("  Error unzipping RGI:", e)

print("Data download completed successfully.")
