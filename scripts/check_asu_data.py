import urllib.request
import ssl
import re

url = "https://www.mars.asu.edu/data/"
ctx = ssl._create_unverified_context()
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("Length:", len(html))
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for l in links:
            if any(k in l.lower() for k in ['tes', 'mineral', 'olivine', 'pyroxene', 'bandfield']):
                print(" ", l)
except Exception as e:
    print("Error:", e)
