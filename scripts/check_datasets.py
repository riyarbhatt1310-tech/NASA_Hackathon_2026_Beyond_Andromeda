"""
TerraTwin Dataset Diagnostic Tool.

Run this script to verify that your actual Moon and Mars DEM files are detected,
properly sized, and readable with memory mapping.

Usage:
    python scripts/check_datasets.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import Config
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader


def main():
    print("=" * 65)
    print(" TerraTwin Planetary Dataset Diagnostic Check")
    print("=" * 65)

    config = Config.load()
    status = config.validate_file_existence()

    print("\n1. File Path Resolution & Existence Status:")
    print(f"  - Moon Raster : {config.get_moon_raster_path()}")
    print(f"    Exists      : {'[OK]' if status['moon_raster'] else '[NOT FOUND]'}")
    print(f"  - Moon Label  : {config.get_moon_label_path()}")
    print(f"    Exists      : {'[OK]' if status['moon_label'] else '[NOT FOUND]'}")
    print(f"  - Mars Raster : {config.get_mars_raster_path()}")
    print(f"    Exists      : {'[OK]' if status['mars_raster'] else '[NOT FOUND]'}")
    print(f"  - Mars Metadata: {config.get_mars_metadata_path()}")
    print(f"    Exists      : {'[OK]' if status['mars_metadata'] else '[NOT FOUND]'}")

    print("\n2. Dataset Verification:")
    if status["moon_raster"]:
        try:
            with MoonLolaReader(config.get_moon_raster_path(), config.get_moon_label_path()) as reader:
                print(f"  [Moon] Shape: {reader.data.shape}, Dtype: {reader.data.dtype}")
                center_elev = reader.get_elevation_at(0.0, 0.0)
                print(f"  [Moon] Sample elevation at (0 deg N, 0 deg E): {center_elev} m")
                print("  [Moon] Successfully memory-mapped and verified.")
        except Exception as e:
            print(f"  [Moon] Error reading file: {e}")
    else:
        print("  [Moon] To connect your Moon file, update 'moon.raster_path' in config/config.yaml")

    if status["mars_raster"]:
        try:
            with MarsMolaReader(config.get_mars_raster_path(), config.get_mars_metadata_path()) as reader:
                print(f"  [Mars] Shape: {reader.data.shape}, Dtype: {reader.data.dtype}")
                center_elev = reader.get_elevation_at(0.0, 0.0)
                print(f"  [Mars] Sample elevation at (0 deg N, 0 deg E): {center_elev} m")
                print("  [Mars] Successfully memory-mapped and verified.")
        except Exception as e:
            print(f"  [Mars] Error reading file: {e}")
    else:
        print("  [Mars] To connect your Mars file, update 'mars.raster_path' in config/config.yaml")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
