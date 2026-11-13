import urllib.request
import re

url = "http://tes.asu.edu/mineral_map/"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("TES Mineral Map Page length:", len(html))
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for l in links[:30]:
            print(" ", l)
except Exception as e:
    print("Error:", e)
