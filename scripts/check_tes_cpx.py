import urllib.request
import ssl
import re

url = "https://www.mars.asu.edu/data/tes_clinopyroxene/"
ctx = ssl._create_unverified_context()
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        files = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        print("Clinopyroxene files:")
        for f in files:
            if not f.startswith('?'):
                print(" ", f)
except Exception as e:
    print("Error:", e)
