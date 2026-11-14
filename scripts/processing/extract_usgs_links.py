import urllib.request
import re

url = "https://astrogeology.usgs.gov/search/map/Moon/Clementine/UVVIS/Lunar_Clementine_UVVIS_FeO_ColorBinned_1km"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8', errors='ignore')
    matches = re.findall(r'(https?://[^\s"\'<>]+)', html)
    for m in set(matches):
        if any(term in m.lower() for term in ['download', 'tif', 'cub', 'planetarymaps', 'astropedia', 'data']):
            print("Match:", m)
