import json
import urllib.request
import re

def search_usgs(query):
    url = f"https://astrogeology.usgs.gov/api/search?q={query}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return str(e)

print("Searching Clementine FeO:")
res_feo = search_usgs("Clementine+FeO")
print(res_feo if isinstance(res_feo, str) else [item.get('title') for item in res_feo.get('results', [])[:5]])

print("Searching Mars TES mineral:")
res_tes = search_usgs("TES+mineral")
print(res_tes if isinstance(res_tes, str) else [item.get('title') for item in res_tes.get('results', [])[:5]])
