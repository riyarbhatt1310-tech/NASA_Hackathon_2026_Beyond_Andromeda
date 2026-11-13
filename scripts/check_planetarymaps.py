import urllib.request

url = "https://planetarymaps.usgs.gov/mosaic/Lunar_Clementine_UVVIS_Warp_ClrRatio_Global_200m.tif"
try:
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'TerraTwin/1.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        print("ClrRatio Global 200m:", r.status, "Length:", r.getheader("Content-Length"))
except Exception as e:
    print("Error:", e)
