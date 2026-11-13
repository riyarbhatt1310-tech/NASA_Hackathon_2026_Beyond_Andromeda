import urllib.request
import re

url = 'https://astrogeology.usgs.gov/search/map/Moon/Geology/Unified_Geologic_Map_of_the_Moon_GIS'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        for m in re.finditer(r'href="([^"]+)"', html):
            l = m.group(1)
            if any(k in l.lower() for k in ['download', 'zip', 'tif', 'gdb', 'gis', 'astropedia']):
                print(l)
except Exception as e:
    print('Error:', e)
