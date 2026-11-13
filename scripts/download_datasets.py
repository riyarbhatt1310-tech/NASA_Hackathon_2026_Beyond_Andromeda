"""
Download and verify official NASA/MIT planetary DEM datasets for TerraTwin.

Datasets:
- Moon LOLA (LDEM_16_FLOAT.IMG, LDEM_16_FLOAT.LBL) from MIT Imbrium server
- Mars MOLA (megt90n000eb.img, megt90n000eb.xml) from Washington University PDS Geosciences Node
"""

import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOON_DIR = PROJECT_ROOT / "data" / "raw" / "moon"
MARS_DIR = PROJECT_ROOT / "data" / "raw" / "mars"

DOWNLOADS = [
    {
        "name": "Moon LOLA Metadata (LDEM_16_FLOAT.LBL)",
        "url": "https://imbrium.mit.edu/DATA/LOLA_GDR/CYLINDRICAL/FLOAT_IMG/LDEM_16_FLOAT.LBL",
        "dest": MOON_DIR / "LDEM_16_FLOAT.LBL",
        "expected_min_bytes": 1000,
        "exact_bytes": None,
    },
    {
        "name": "Moon LOLA Global DEM (LDEM_16_FLOAT.IMG)",
        "url": "https://imbrium.mit.edu/DATA/LOLA_GDR/CYLINDRICAL/FLOAT_IMG/LDEM_16_FLOAT.IMG",
        "dest": MOON_DIR / "LDEM_16_FLOAT.IMG",
        "expected_min_bytes": 66_000_000,
        "exact_bytes": 2880 * 5760 * 4,  # 66,355,200 bytes
    },
    {
        "name": "Mars MOLA Metadata (megt90n000eb.xml)",
        "url": "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg016/megt90n000eb.xml",
        "dest": MARS_DIR / "megt90n000eb.xml",
        "expected_min_bytes": 1000,
        "exact_bytes": None,
    },
    {
        "name": "Mars MOLA Global DEM (megt90n000eb.img)",
        "url": "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg016/megt90n000eb.img",
        "dest": MARS_DIR / "megt90n000eb.img",
        "expected_min_bytes": 33_000_000,
        "exact_bytes": 2880 * 5760 * 2,  # 33,177,600 bytes
    },
]


def download_file(item: dict) -> bool:
    dest: Path = item["dest"]
    url: str = item["url"]
    name: str = item["name"]
    exact_bytes = item.get("exact_bytes")
    min_bytes = item.get("expected_min_bytes", 1)

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if already present and valid
    if dest.is_file():
        cur_size = dest.stat().st_size
        if exact_bytes and cur_size == exact_bytes:
            print(f"[SKIP] {name} already exists with exact size ({cur_size:,} bytes).")
            return True
        elif not exact_bytes and cur_size >= min_bytes:
            print(f"[SKIP] {name} already exists ({cur_size:,} bytes).")
            return True
        else:
            print(f"[RETRY] {name} exists but size is incomplete ({cur_size:,} bytes). Re-downloading...")

    print(f"[DOWNLOADING] {name} from:\n  {url}")
    temp_dest = dest.with_suffix(dest.suffix + ".part")

    headers = {"User-Agent": "TerraTwin-NASA-SpaceApps/1.0"}
    req = urllib.request.Request(url, headers=headers)

    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as response, open(temp_dest, "wb") as out_file:
            total_size = response.getheader("Content-Length")
            total_size = int(total_size) if total_size else None
            downloaded = 0
            chunk_size = 1024 * 512  # 512 KB chunks

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    print(f"\r  Progress: {mb:.1f} MB / {total_mb:.1f} MB ({percent:.1f}%)", end="", flush=True)
                else:
                    mb = downloaded / (1024 * 1024)
                    print(f"\r  Downloaded: {mb:.1f} MB", end="", flush=True)

        print()  # newline
        # Rename part to final dest
        if temp_dest.is_file():
            if dest.is_file():
                dest.unlink()
            temp_dest.rename(dest)

        elapsed = time.time() - start_time
        final_size = dest.stat().st_size
        print(f"  [SUCCESS] Saved to {dest} ({final_size:,} bytes in {elapsed:.1f}s)")

        # Verify size
        if exact_bytes and final_size != exact_bytes:
            raise ValueError(f"Size mismatch: got {final_size} bytes, expected {exact_bytes} bytes!")

        return True

    except Exception as e:
        print(f"\n  [ERROR] Failed to download {name}: {e}")
        if temp_dest.is_file():
            temp_dest.unlink()
        return False


def main():
    print("=" * 65)
    print(" TerraTwin Planetary Dataset Downloader & Verifier")
    print("=" * 65)

    all_ok = True
    for item in DOWNLOADS:
        ok = download_file(item)
        if not ok:
            all_ok = False
            print(f"\nTerminating due to error downloading {item['name']}.")
            sys.exit(1)

    print("\nAll datasets downloaded and verified successfully!")


if __name__ == "__main__":
    main()
