import urllib.request

url = "https://doi.pangaea.de/10.1594/PANGAEA.788537?format=textfile"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print("Pangaea textfile status:", r.status, "Length:", r.getheader("Content-Length"))
        header = [r.readline().decode('utf-8', errors='ignore') for _ in range(15)]
        print("Header sample:")
        for h in header:
            print(" ", h.strip())
except Exception as e:
    print("Error:", e)
