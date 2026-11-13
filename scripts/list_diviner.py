import urllib.request
import re

url = 'https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/geotiff/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')

print('GHRM GeoTIFFs:')
for m in re.finditer(r'href="([^"]+\.tif)"', html):
    print(m.group(1))

url2 = 'https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gdr_l3/'
try:
    req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2) as resp2:
        html2 = resp2.read().decode('utf-8')
    print('GDR L3 files:')
    for m in re.finditer(r'href="([^"]+)"', html2):
        if not m.group(1).startswith('?') and not m.group(1).startswith('/'):
            print(m.group(1))
except Exception as e:
    print('GDR L3 error:', e)
