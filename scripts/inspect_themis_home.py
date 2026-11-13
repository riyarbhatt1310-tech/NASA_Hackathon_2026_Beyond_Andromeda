import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://themis.asu.edu/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I):
    href = m.group(1)
    text = m.group(2).strip()
    if any(k in href.lower() or k in text.lower() for k in ['themis', 'thermal', 'map', 'data', 'mosaic', 'download', 'image']):
        print(href, '-->', text[:60])
