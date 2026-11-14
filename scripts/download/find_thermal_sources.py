"""
Find exact URLs for Diviner, THEMIS, TES on PDS Geosciences.
"""

import urllib.request
import re
import ssl

ctx = ssl._create_unverified_context()
headers = {'User-Agent': 'Mozilla/5.0'}

def check_page(url, label):
    print(f"\n=== {label}: {url} ===")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
            for l in links:
                if any(k in l.lower() for k in ['gdr', 'thermal', 'temp', 'bolom', 'inertia', 'browse', 'derived']):
                    print("  ", l)
    except Exception as e:
        print(f"Error {label}: {e}")

check_page("https://pds-geosciences.wustl.edu/missions/lro/diviner.htm", "LRO Diviner")
check_page("https://pds-geosciences.wustl.edu/missions/mgs/tes.htm", "MGS TES")
check_page("https://pds-geosciences.wustl.edu/missions/odyssey/themis.htm", "Odyssey THEMIS")
