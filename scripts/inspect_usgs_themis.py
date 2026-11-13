import urllib.request
import re

url = 'https://astrogeology.usgs.gov/search/map/themis_thermal_inertia_mosaic_quantitative_30n060e_100mpp'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

print('Title:')
for t in re.findall(r'<title>(.*?)</title>', html):
    print(t)

print('Links:')
for m in re.finditer(r'href="([^"]+)"', html):
    l = m.group(1)
    if any(k in l.lower() for k in ['tif', 'cub', 'download', 'astropedia', 'planetarymaps']):
        print(l)
