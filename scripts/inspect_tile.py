"""
Inspect Geomorphometry of any 25 km Tile on Moon or Mars using Real Planetary DEMs.

Usage:
    python scripts/inspect_tile.py --body moon --lat -89.5 --lon 0.0
    python scripts/inspect_tile.py --body mars --lat 18.65 --lon 226.2
    python scripts/inspect_tile.py --body mars --lat 18.38 --lon 77.58
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import Config
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader
from src.processing.tile_extractor import PlanetaryTileExtractor


def main():
    parser = argparse.ArgumentParser(description="Inspect 25 km Planetary Tile Geomorphometry")
    parser.add_argument("--body", type=str, choices=["moon", "mars"], default="mars", help="Planetary body")
    parser.add_argument("--lat", type=float, default=18.65, help="Center latitude [-90 to +90]")
    parser.add_argument("--lon", type=float, default=226.2, help="Center longitude [0 to 360]")
    args = parser.parse_args()

    cfg = Config.load()
    body = args.body.lower()

    print("=" * 70)
    print(f" TerraTwin Geomorphometry Tile Inspection: {body.upper()} at ({args.lat} deg N, {args.lon} deg E)")
    print("=" * 70)

    moon_reader = None
    mars_reader = None

    if body == "moon":
        moon_reader = MoonLolaReader(cfg.get_moon_raster_path(), cfg.get_moon_label_path()).open()
    else:
        mars_reader = MarsMolaReader(cfg.get_mars_raster_path(), cfg.get_mars_metadata_path()).open()

    try:
        extractor = PlanetaryTileExtractor(moon_reader=moon_reader, mars_reader=mars_reader)
        if body == "moon":
            record = extractor.extract_moon_tile(args.lat, args.lon)
        else:
            record = extractor.extract_mars_tile(args.lat, args.lon)

        print(f"\n1. Spatial Geodesy & Analysis Tile Footprint:")
        print(f"   Tile ID              : {record['tile_id']}")
        print(f"   Center (Lat, Lon)    : ({record['lat_center']} deg N, {record['lon_center']} deg E)")
        print(f"   Bounding Box         : Lat [{record['lat_min']} to {record['lat_max']}], Lon [{record['lon_min']} to {record['lon_max']}]")
        print(f"   Physical Cell Area   : {record['actual_area_km2']:.2f} km^2 (~25 km x 25 km target: 625 km^2)")
        print(f"   Native Resolution    : {record['native_res_km']:.4f} km/pixel")
        print(f"   Effective Resolution : {record['effective_res_km']:.4f} km/pixel")
        print(f"   Valid Samples in Tile: {record['sample_count']:,} native pixels")

        print(f"\n2. Parameter Group 1: Terrain Geomorphometry:")
        print(f"   Valid Data Coverage  : {record['terrain_coverage_pct']}% (Valid: {record['terrain_valid']})")
        if record["terrain_valid"]:
            print(f"   Mean Elevation       : {record['terrain_mean_elevation_m']:+,.1f} m")
            print(f"   Elevation Std Dev    : {record['terrain_std_elevation_m']:,.1f} m")
            print(f"   Local Relief (Max-Min: {record['terrain_local_relief_m']:,.1f} m")
            print(f"   Mean Physical Slope  : {record['terrain_mean_slope_deg']:.2f} deg")
            print(f"   95th Pct Slope       : {record['terrain_max_slope_deg']:.2f} deg")
            print(f"   Terrain Roughness    : {record['terrain_roughness_index_m']:.1f} m (TRI)")
            print(f"   Hypsometric Integral : {record['terrain_hypsometric_integral']:.3f} (0=degraded floor, 1=youthful plateau)")
            print(f"   Hypsometric Skewness : {record['terrain_hypsometric_skewness']:+.3f}")
        else:
            print(f"   [INSUFFICIENT COVERAGE: < 70% valid data pixels]")

        print(f"\n3. Multi-Parameter Architecture Status:")
        print(f"   - Group 2 (Mineralogy) : Ready for ingestion in Milestone 3")
        print(f"   - Group 3 (Thermal)    : Ready for ingestion in Milestone 3")
        print(f"   - Group 4 (Water/Ice)  : Ready for ingestion in Milestone 3")
        print(f"   - Group 5 (Geology)    : Ready for ingestion in Milestone 3")
        print("=" * 70)

    finally:
        if moon_reader:
            moon_reader.close()
        if mars_reader:
            mars_reader.close()


if __name__ == "__main__":
    main()
