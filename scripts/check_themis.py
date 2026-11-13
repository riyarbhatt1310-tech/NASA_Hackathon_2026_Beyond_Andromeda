import urllib.request
import re

url = 'https://pds-geosciences.wustl.edu/missions/odyssey/themis.html'
with urllib.request.urlopen(url) as resp:
    html = resp.read().decode('utf-8')

for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I):
    if any(k in m.group(0).lower() for k in ['themis', 'node', 'volume', 'online', 'data']):
        print(m.group(1), '-->', m.group(2).strip())
