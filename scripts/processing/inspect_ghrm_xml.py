"""
Inspect XML label of Diviner GHRM GeoTIFF.
"""

import urllib.request

url = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/geotiff/dghrm_tbol_sam_70s70n_tif.xml"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        text = r.read().decode('utf-8')
        print("XML size:", len(text))
        for line in text.split('\n'):
            if any(k in line.lower() for k in ['scaling_factor', 'value_offset', 'unit', 'description', 'special_constants', 'valid_minimum', 'valid_maximum', 'nodata']):
                print(" ", line.strip())
except Exception as e:
    print("Error:", e)
