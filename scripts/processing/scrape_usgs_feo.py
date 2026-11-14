import urllib.request
import re

url = "https://astrogeology.usgs.gov/search/map/Moon/Clementine/UVVIS/Lunar_Clementine_UVVIS_FeO_ColorBinned_1km"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8')
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("Page links on USGS FeO:")
        for l in links:
            if any(ext in l.lower() for ext in ['.tif', '.cub', '.tar', '.gz', '.zip', '.lbl', 'download']):
                print(" ", l)
except Exception as e:
    print("Error:", e)
