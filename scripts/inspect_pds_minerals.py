import urllib.request
import re

for rel in ['../grsfe/index.htm', 'tes.html']:
    url = f"https://pds-geosciences.wustl.edu/missions/mgs/{rel}" if not rel.startswith('..') else f"https://pds-geosciences.wustl.edu/{rel[3:]}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8')
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
            print(f"=== {url} ===")
            for l in links[:15]:
                print(" ", l)
    except Exception as e:
        print("Error accessing", url, ":", e)
