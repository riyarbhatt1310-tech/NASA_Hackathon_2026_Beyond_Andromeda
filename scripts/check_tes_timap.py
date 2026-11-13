import urllib.request
import re

url = 'https://pds-geosciences.wustl.edu/missions/mgs/tes.html'
with urllib.request.urlopen(url) as resp:
    html = resp.read().decode('utf-8')

for line in html.splitlines():
    if 'bolom' in line.lower() or 'temperature' in line.lower() or 'mgst_' in line.lower():
        print(line.strip()[:140])
