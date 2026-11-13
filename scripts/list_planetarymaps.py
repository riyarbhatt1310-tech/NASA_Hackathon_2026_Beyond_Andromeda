import urllib.request
import re

url = "https://planetarymaps.usgs.gov/mosaic/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("Planetarymaps files count:", len(files))
        matches = [f for f in files if any(k in f.lower() for k in ['fe', 'mineral', 'clem', 'tes', 'mola', 'mars', 'lunar'])]
        print("Planetarymaps matches:")
        for m in matches[:30]:
            print(" ", m)
except Exception as e:
    print("Error:", e)
