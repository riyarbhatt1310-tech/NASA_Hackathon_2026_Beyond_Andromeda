import urllib.request
import re

url = "https://doi.pangaea.de/10.1594/PANGAEA.788537"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("PANGAEA length:", len(html))
        # Find download links (tab delimited, zip, etc.)
        links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
        for l in links:
            if any(term in l.lower() for term in ['download', 'zip', 'tab', 'txt']):
                print(" ", l)
except Exception as e:
    print("Error:", e)
