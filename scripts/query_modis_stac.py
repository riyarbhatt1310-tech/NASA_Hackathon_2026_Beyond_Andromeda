"""
Query Microsoft Planetary Computer for open MOD11A1 GeoTIFF.
"""

import urllib.request
import json

stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1/collections/modis-11A1-061/items?limit=1"
req = urllib.request.Request(stac_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
        features = data.get('features', [])
        print("Features found:", len(features))
        if features:
            item = features[0]
            print("Item ID:", item.get('id'))
            print("Date:", item.get('properties', {}).get('datetime'))
            assets = item.get('assets', {})
            for name, asset in assets.items():
                if any(k in name for k in ['LST_Day', 'LST_Night', 'QC_Day', 'QC_Night']):
                    print(f"  {name}: {asset.get('href')}")
except Exception as e:
    print("Error:", e)
