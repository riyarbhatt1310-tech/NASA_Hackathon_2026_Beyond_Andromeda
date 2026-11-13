import urllib.request
import re

url = "https://pds-geosciences.wustl.edu/missions/mgs/tes_special.html"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8')
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("TES Special links:")
        for l in links[:20]:
            print(" ", l)
except Exception as e:
    print("Error accessing tes_special.html:", e)
