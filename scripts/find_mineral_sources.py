import re
import urllib.request

def check_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)

# 1. Check MGS directory
status, content = check_url('https://pds-geosciences.wustl.edu/mgs/')
print('MGS status:', status)
if content:
    tes_links = [m for m in re.findall(r'href=[\'"]([^\'"]+)[\'"]', content) if 'tes' in m.lower()]
    print('TES links:', tes_links)

# 2. Check Clementine
status_clem, content_clem = check_url('https://pds-geosciences.wustl.edu/missions/clementine/')
print('Clementine status:', status_clem)
if content_clem:
    clem_links = [m for m in re.findall(r'href=[\'"]([^\'"]+)[\'"]', content_clem) if any(k in m.lower() for k in ['fe', 'mineral', 'map', 'ti', 'uvvis'])]
    print('Clementine mineral links:', clem_links)
