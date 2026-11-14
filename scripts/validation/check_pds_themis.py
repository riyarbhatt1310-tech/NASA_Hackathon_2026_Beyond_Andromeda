import urllib.request
import re

url = 'http://static.mars.asu.edu/pds/ODTGEO_v2/data/odtip2_0001/'
with urllib.request.urlopen(url) as resp:
    html = resp.read().decode('utf-8')

print('Items in odtip2_0001:')
for m in re.finditer(r'<a href="([^"]+)"', html):
    h = m.group(1)
    if not h.startswith('.'):
        print(' ', h)
