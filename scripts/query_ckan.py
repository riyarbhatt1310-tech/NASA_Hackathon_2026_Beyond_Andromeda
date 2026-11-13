import urllib.request
import json

url = "https://astrogeology.usgs.gov/ckan/api/3/action/package_search?q=Clementine+FeO"
req = urllib.request.Request(url, headers={'User-Agent': 'TerraTwin/1.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
        results = data.get('result', {}).get('results', [])
        print("CKAN Results count:", len(results))
        for res in results[:5]:
            print("Title:", res.get('title'))
            for res_item in res.get('resources', []):
                print("  Resource:", res_item.get('name'), "->", res_item.get('url'))
except Exception as e:
    print("CKAN error:", e)
