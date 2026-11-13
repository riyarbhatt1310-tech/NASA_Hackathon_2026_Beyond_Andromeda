import urllib.request
import ssl

for name in ['TiO2', 'Omat', 'Albedo']:
    url = f"https://planetarymaps.usgs.gov/mosaic/Lunar_Clementine_UVVIS_{name}_ClrBinned_70S70N_1km.tif"
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            print(f"Lunar Clementine {name}:", r.status, "Length:", r.getheader("Content-Length"))
    except Exception as e:
        print(f"Lunar Clementine {name}: {e}")
