"""
Inspect Diviner GDR and GHRM files on PDS Geosciences.
"""

import urllib.request
import re

for sub in ['data_derived_ghrm', 'data_derived_gdr_l2', 'data_derived_pcp']:
    url = f"https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/{sub}/"
    print(f"\n=== Checking {sub} ===")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8')
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html, re.I)
            print(f"Links count: {len(links)}")
            for l in links[:15]:
                if not l.endswith('/'):
                    print("  ", l)
    except Exception as e:
        print(f"Error {sub}: {e}")
