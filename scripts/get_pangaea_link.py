import urllib.request
import re

url = "https://doi.pangaea.de/10.1594/PANGAEA.788537"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    html = r.read().decode('utf-8', errors='ignore')
    matches = re.findall(r'href=[\'"]([^\'"]*download[^\'"]*)[\'"]', html, re.IGNORECASE)
    print("Matches:", matches)
    all_links = [l for l in re.findall(r'href=[\'"]([^\'"]+)[\'"]', html) if '788537' in l or 'datasets' in l]
    print("Dataset links:", all_links)
