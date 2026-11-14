import urllib.request
import json
import xml.etree.ElementTree as ET

# Query ODE REST API for THEMIS thermal products or MGS TES products
# http://oderest.rsl.wustl.edu/live2/?target=mars&query=product&pt=TI&results=x
# Or query PDS Geosciences MGS TES archive

urls = [
    'http://oderest.rsl.wustl.edu/live2/?target=mars&query=product&pt=TI&results=x&limit=5',
    'http://oderest.rsl.wustl.edu/live2/?target=mars&query=product&pt=BOLTEMP&results=x&limit=5',
    'http://oderest.rsl.wustl.edu/live2/?target=moon&query=product&pt=GHRM&results=x&limit=5',
    'https://pds-geosciences.wustl.edu/lro/lro-l-dlre-5-ghrm-v1/lrodlr_1001/data_derived_ghrm/',
    'https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-derived-v1/mgst_1101/'
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print(u, '-> Status:', resp.status, 'Len:', len(content))
            if b'<?xml' in content[:50]:
                root = ET.fromstring(content)
                for prod in root.findall('.//Product'):
                    p_id = prod.findtext('Product_id')
                    files = [f.findtext('URL') for f in prod.findall('.//Product_files/Product_file')]
                    print('  Prod:', p_id, files[:2])
    except Exception as e:
        print(u, '-> Error:', e)
