import urllib.request
import re

url = "https://pds-geosciences.wustl.edu/missions/mgs/"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8')
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("MGS mission page links:")
        for l in links:
            if 'mola' in l.lower() or 'tes' in l.lower() or 'grs' in l.lower() or 'data' in l.lower():
                print(" ", l)
except Exception as e:
    print("Error:", e)
