"""
Inspect GeoTIFF files in Diviner GHRM directory.
"""

import urllib.request
import re

url = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/geotiff/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8')
    links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html, re.I)
    print(f"Total links: {len(links)}")
    for l in links:
        if not l.endswith('/'):
            print(" ", l)
