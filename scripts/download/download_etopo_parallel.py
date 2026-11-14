import concurrent.futures
import threading
import time
import urllib.request
from pathlib import Path

URL = "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif"
DEST_DIR = Path(r"C:\Users\maitr\.gemini\antigravity\scratch\terratwin\data\raw\earth\dem")
DEST_DIR.mkdir(parents=True, exist_ok=True)
DEST_FILE = DEST_DIR / "ETOPO_2022_v1_60s_N90W180_surface.tif"
NUM_WORKERS = 12
CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

def get_file_size(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 TerraTwin/0.1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return int(resp.headers.get("Content-Length", 0))

def fetch_chunk(url, start_byte, end_byte):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 TerraTwin/0.1.0",
            "Range": f"bytes={start_byte}-{end_byte}"
        }
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read()
    return start_byte, data

def main():
    total_size = get_file_size(URL)
    print(f"Total file size: {total_size} bytes ({total_size / (1024*1024):.2f} MB)", flush=True)
    
    chunks = []
    for start in range(0, total_size, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE - 1, total_size - 1)
        chunks.append((start, end))
        
    print(f"Divided into {len(chunks)} chunks across {NUM_WORKERS} workers.", flush=True)
    
    # Open destination file once for writing
    with open(DEST_FILE, "wb") as out_f:
        out_f.truncate(total_size)
    
    file_lock = threading.Lock()
    out_f = open(DEST_FILE, "r+b")
    
    t0 = time.time()
    downloaded = 0
    last_report = t0
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            future_to_chunk = {
                executor.submit(fetch_chunk, URL, start, end): (start, end)
                for start, end in chunks
            }
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                start, end = future_to_chunk[future]
                try:
                    start_byte, data = future.result()
                    with file_lock:
                        out_f.seek(start_byte)
                        out_f.write(data)
                        out_f.flush()
                    downloaded += len(data)
                    
                    now = time.time()
                    if now - last_report > 3 or downloaded == total_size:
                        mb = downloaded / (1024 * 1024)
                        pct = (downloaded / total_size) * 100
                        rate = mb / (now - t0 + 1e-5)
                        print(f"Downloaded {mb:.1f} MB / {total_size/(1024*1024):.1f} MB ({pct:.1f}%) at {rate:.2f} MB/s", flush=True)
                        last_report = now
                except Exception as e:
                    print(f"Error on chunk {start}-{end}: {e}. Retrying...", flush=True)
                    # Retry once
                    try:
                        time.sleep(1)
                        start_byte, data = fetch_chunk(URL, start, end)
                        with file_lock:
                            out_f.seek(start_byte)
                            out_f.write(data)
                            out_f.flush()
                        downloaded += len(data)
                    except Exception as e2:
                        print(f"Permanent failure on chunk {start}-{end}: {e2}", flush=True)
    finally:
        out_f.close()

    t1 = time.time()
    final_size = DEST_FILE.stat().st_size
    print(f"Download completed in {t1 - t0:.1f}s. Final size: {final_size} bytes.", flush=True)
    assert final_size == total_size, f"Size mismatch: {final_size} vs {total_size}"

if __name__ == "__main__":
    main()
