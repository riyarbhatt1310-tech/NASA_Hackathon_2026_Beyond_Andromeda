import urllib.request

url = "https://astrogeology.usgs.gov/search/map/Moon/Clementine/UVVIS/Lunar_Clementine_UVVIS_FeO_ColorBinned_1km"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print("Final URL:", r.geturl())
        content = r.read().decode('utf-8', errors='ignore')
        print("Content length:", len(content))
        print("First 500 chars:", content[:500])
except Exception as e:
    print("Error:", e)
