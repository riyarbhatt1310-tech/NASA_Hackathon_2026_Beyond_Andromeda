"""
Inspect South Pole diurnal polar cumulative products.
"""

import urllib.request
import re

url = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/diurnal/ltim/pols/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8')
    links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html, re.I)
    print(f"Total links: {len(links)}")
    for l in links[:30]:
        if not l.endswith('/'):
            print(" ", l)
