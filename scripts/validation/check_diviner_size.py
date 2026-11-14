"""
Check exact sizes of Diviner day and night GeoTIFFs.
"""

import urllib.request

base = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/geotiff/"
for name in ["dghrm_tbol_sam_70s70n_tif.tif", "dghrm_tbol_m_70s70n_tif.tif", "dghrm_ra_sam_70s70n_tif.tif"]:
    req = urllib.request.Request(base + name, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            size_mb = int(r.getheader('Content-Length')) / (1024 * 1024)
            print(f"{name}: {size_mb:.2f} MB")
    except Exception as e:
        print(f"Error {name}: {e}")
