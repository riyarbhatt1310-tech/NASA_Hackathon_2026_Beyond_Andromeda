import urllib.request
import re

url = 'http://themis-data.mars.asu.edu/'
with urllib.request.urlopen(url) as resp:
    html = resp.read().decode('utf-8')

for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I):
    href = m.group(1)
    text = m.group(2).strip()
    if any(k in href.lower() or k in text.lower() for k in ['mosaic', 'thermal', 'inertia', 'data', 'download', 'products', 'map', 'ir']):
        print(href, '-->', text[:60])
