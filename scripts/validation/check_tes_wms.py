import urllib.request
import ssl

for mineral in ['TES_Clinopyroxene', 'TES_Olivine', 'TES_Plagioclase']:
    url = f"http://ms-mars.mars.asu.edu/{mineral}?SERVICE=WMS&REQUEST=GetMap&FORMAT=image/png&WIDTH=720&HEIGHT=360&SRS=JMARS:4&BBOX=-180,-90,180,90&STYLES=&VERSION=1.1.1&LAYERS={mineral}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"Mars {mineral}: HTTP {r.status}, Length: {r.getheader('Content-Length')}")
    except Exception as e:
        print(f"Mars {mineral}: {e}")
