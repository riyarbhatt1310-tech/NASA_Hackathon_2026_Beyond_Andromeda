"""
Query Zenodo API for THEMIS thermal inertia GeoTIFF files.
"""

import urllib.request
import json

url = "https://zenodo.org/api/records?q=%22A+new+global+thermal+inertia+map+of+Mars%22"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
        hits = data.get('hits', {}).get('hits', [])
        print(f"Total hits: {len(hits)}")
        for h in hits:
            print(f"Record: {h.get('id')} - {h.get('metadata', {}).get('title')}")
            files = h.get('files', [])
            print(f"  Files count: {len(files)}")
            for f in files[:10]:
                print(f"    {f.get('key')} - {f.get('size') / (1024*1024):.2f} MB - {f.get('links', {}).get('self')}")
except Exception as e:
    print(f"Error querying Zenodo: {e}")
