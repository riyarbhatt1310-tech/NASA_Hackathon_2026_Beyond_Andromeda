import urllib.request
import re

url = 'http://global-data.mars.asu.edu/bin/themis.pl'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Search for file paths, download URLs, or base URLs in javascript
print("JS variables in themis.pl:")
for line in html.splitlines():
    if any(k in line.lower() for k in ['base', 'url', 'path', 'cgi', 'ti', 'inertia', 'quad', 'layer']):
        print(line.strip()[:140])
