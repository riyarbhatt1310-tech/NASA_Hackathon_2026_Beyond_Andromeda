"""Global Earth Analog Tile Catalog and Spatial Indexer.

Generates, caches, and indexes a diverse, scientifically curated global repository
of terrestrial candidate tiles covering:
- Major planetary analog sites (Atacama, McMurdo Dry Valleys, Devon Island, Iceland, Mojave, Sahara, etc.)
- Confirmed hypervelocity impact structures (Sudbury, Vredefort, Meteor Crater, Ries, Lonar, etc.)
- Flood basalts and volcanic fields (Deccan, Columbia River, Iceland, Hawaii, Kamchatka)
- Polar cryosphere and glaciated regions (Greenland, Antarctica, Alaska, Svalbard)
- Systematic continental grid sampling across all continents.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import numpy as np

from src.core.grids import PlanetaryGrid, PlanetaryTile
from src.core.constants import EARTH_VOLUMETRIC_RADIUS_M
from src.core.metrics import compute_tile_geomorphometry
from src.processing.tile_extractor import PlanetaryTileExtractor
from src.data_ingestion.earth_water import EarthWaterAggregator
from src.data_ingestion.earth_impacts import EarthImpactCatalog
from src.data_ingestion.earth_glim import EarthGLiMAggregator
from src.data_ingestion.earth_modis import ModisLSTReader
from src.data_ingestion.earth_dem import EarthDemReader


# Curated high-priority planetary analog target coordinates on Earth
CURATED_EARTH_ANALOG_SITES = [
    # North America
    {"name": "Death Valley / Mojave Desert, USA", "lat": 36.53, "lon": -116.93, "category": "desert_basin"},
    {"name": "Meteor Crater (Barringer), Arizona, USA", "lat": 35.03, "lon": -111.02, "category": "impact_crater"},
    {"name": "Sudbury Impact Basin, Ontario, Canada", "lat": 46.60, "lon": -81.18, "category": "impact_basin"},
    {"name": "Columbia River Basalt Plateau, USA", "lat": 46.85, "lon": -119.50, "category": "flood_basalt"},
    {"name": "St. Elias / Malaspina Glacier, Alaska, USA", "lat": 60.00, "lon": -140.50, "category": "glacier"},
    {"name": "Devon Island / Haughton Crater, Nunavut, Canada", "lat": 75.38, "lon": -89.67, "category": "polar_desert_impact"},
    {"name": "Manicouagan Impact Structure, Quebec, Canada", "lat": 51.38, "lon": -68.70, "category": "impact_crater"},
    {"name": "Grand Canyon Lithologies, Arizona, USA", "lat": 36.10, "lon": -112.11, "category": "stratigraphy"},
    # South America
    {"name": "Atacama Desert (Yungay Hyper-Arid Plain), Chile", "lat": -24.08, "lon": -70.00, "category": "hyper_arid_desert"},
    {"name": "Salar de Uyuni Evaporite Basin, Bolivia", "lat": -20.13, "lon": -67.49, "category": "playa_evaporite"},
    {"name": "Altiplano Volcanic Plateau, Chile/Bolivia", "lat": -22.50, "lon": -67.80, "category": "volcanic_plateau"},
    {"name": "Paraná Flood Basalt Province, Brazil", "lat": -25.00, "lon": -52.00, "category": "flood_basalt"},
    {"name": "Southern Patagonian Icefield, Chile", "lat": -49.00, "lon": -73.50, "category": "glacier_sheet"},
    # Africa
    {"name": "Richat Structure (Eye of the Sahara), Mauritania", "lat": 21.13, "lon": -11.40, "category": "domal_uplift"},
    {"name": "Vredefort Giant Impact Structure, South Africa", "lat": -27.00, "lon": 27.50, "category": "impact_basin"},
    {"name": "Danakil Depression Hydrothermal Basin, Ethiopia", "lat": 14.24, "lon": 40.30, "category": "hydrothermal_rift"},
    {"name": "Sahara Desert (Erg Chebbi Basalt & Sand), Morocco", "lat": 31.18, "lon": -3.97, "category": "desert_dune"},
    {"name": "Tibesti Volcanic Massif, Chad", "lat": 20.80, "lon": 17.50, "category": "volcanic_shield"},
    {"name": "Namib Desert Hyper-Arid Dunes, Namibia", "lat": -24.75, "lon": 15.28, "category": "hyper_arid_desert"},
    {"name": "East African Rift (Ol Doinyo Lengai), Tanzania", "lat": -2.76, "lon": 35.91, "category": "continental_rift"},
    # Europe & Arctic
    {"name": "Askja / Dyngjufjöll Volcanic Caldera, Iceland", "lat": 65.03, "lon": -16.75, "category": "basaltic_caldera"},
    {"name": "Vatnajökull Subglacial Volcanoes, Iceland", "lat": 64.40, "lon": -16.80, "category": "glaciovolcanic"},
    {"name": "Nördlinger Ries Impact Crater, Germany", "lat": 48.88, "lon": 10.55, "category": "impact_crater"},
    {"name": "Svalbard Permafrost & Glaciers, Norway", "lat": 78.22, "lon": 15.65, "category": "arctic_permafrost"},
    {"name": "Rio Tinto Iron-Sulfate Basin, Spain", "lat": 37.69, "lon": -6.56, "category": "acid_sulfate_mars_analog"},
    # Asia
    {"name": "Gobi Desert (Nemegt Arid Basin), Mongolia", "lat": 43.50, "lon": 101.00, "category": "continental_desert"},
    {"name": "Taklamakan Desert Basins, China", "lat": 38.90, "lon": 83.60, "category": "arid_basin"},
    {"name": "Tibetan Plateau / Qaidam Basin, China", "lat": 37.20, "lon": 95.00, "category": "high_altitude_playa"},
    {"name": "Deccan Traps Continental Flood Basalts, India", "lat": 19.00, "lon": 74.00, "category": "flood_basalt"},
    {"name": "Lonar Impact Crater in Basalt, India", "lat": 19.98, "lon": 76.51, "category": "basaltic_impact_crater"},
    {"name": "Kamchatka Volcanic Zone, Russia", "lat": 55.00, "lon": 160.00, "category": "subduction_volcanic"},
    {"name": "Dasht-e Lut Thermal Extreme Desert, Iran", "lat": 30.60, "lon": 58.80, "category": "thermal_extreme_desert"},
    # Australia
    {"name": "Pilbara Ancient Archean Crust, Western Australia", "lat": -21.50, "lon": 119.50, "category": "ancient_craton"},
    {"name": "Gosses Bluff Impact Crater, Northern Territory, Australia", "lat": -23.82, "lon": 132.31, "category": "impact_crater"},
    {"name": "Wolfe Creek Meteorite Crater, Western Australia", "lat": -19.17, "lon": 127.79, "category": "impact_crater"},
    {"name": "Lake Eyre Ephemeral Playa, South Australia", "lat": -28.37, "lon": 137.37, "category": "playa_basin"},
    {"name": "Nullarbor Carbonate Plain, Australia", "lat": -31.00, "lon": 127.00, "category": "karst_plain"},
    # Antarctica
    {"name": "McMurdo Dry Valleys (Taylor Valley), Antarctica", "lat": -77.62, "lon": 163.00, "category": "polar_hyper_arid"},
    {"name": "Mount Erebus Anorthoclase Volcano, Antarctica", "lat": -77.53, "lon": 167.17, "category": "polar_volcano"},
    {"name": "Transantarctic Nunataks, Antarctica", "lat": -85.00, "lon": 175.00, "category": "glacial_nunatak"},
]


class EarthCatalogManager:
    """Builds, persists, and queries the global Earth candidate analog catalog."""

    def __init__(self, catalog_path: Optional[str] = None):
        _p = Path(__file__).resolve()
        if len(_p.parents) > 3 and (_p.parents[3] / "data").exists():
            base_dir = _p.parents[3]
        elif len(_p.parents) > 2 and (_p.parents[2] / "data").exists():
            base_dir = _p.parents[2]
        else:
            base_dir = _p.parent

        if catalog_path:
            self.catalog_file = Path(catalog_path)
        elif (base_dir / "data" / "catalogs" / "earth_analog_catalog.json").exists():
            self.catalog_file = base_dir / "data" / "catalogs" / "earth_analog_catalog.json"
        else:
            self.catalog_file = base_dir / "data" / "processed" / "earth_analog_catalog.json"

        self.catalog_file.parent.mkdir(parents=True, exist_ok=True)
        self._catalog: List[Dict[str, Any]] = []
        self._load_or_build()

    def _load_or_build(self) -> None:
        """Loads cached catalog from disk, or generates it if missing."""
        if self.catalog_file.exists():
            try:
                with open(self.catalog_file, "r", encoding="utf-8") as f:
                    self._catalog = json.load(f)
                if len(self._catalog) >= 30:
                    return
            except Exception:
                self._catalog = []

        self._build_and_save_catalog()

    def _build_and_save_catalog(self) -> None:
        """Extracts and persists real multi-parameter features for curated Earth analogs."""
        base_dir = Path(__file__).resolve().parent.parent.parent
        raw_dir = base_dir / "data" / "raw"

        # Initialize available Earth readers
        glim_path = raw_dir / "earth" / "mineralogy" / "glim_global.tif"
        glim_agg = EarthGLiMAggregator(str(glim_path)) if glim_path.exists() else None

        modis_day = raw_dir / "earth" / "thermal" / "modis_lst_day.tif"
        modis_night = raw_dir / "earth" / "thermal" / "modis_lst_night.tif"
        modis_qc_day = raw_dir / "earth" / "thermal" / "modis_qc_day.tif"
        modis_qc_night = raw_dir / "earth" / "thermal" / "modis_qc_night.tif"
        modis_r = ModisLSTReader(
            str(modis_day), str(modis_night), str(modis_qc_day), str(modis_qc_night)
        ) if modis_day.exists() else None

        water_agg = EarthWaterAggregator()
        impact_cat = EarthImpactCatalog()
        dem_path = raw_dir / "earth" / "dem" / "ETOPO_2022_v1_60s_N90W180_surface.tif"
        dem_reader = EarthDemReader(dem_path) if dem_path.exists() else None

        extractor = PlanetaryTileExtractor(
            earth_dem_reader=dem_reader,
            earth_glim_aggregator=glim_agg,
            earth_modis_reader=modis_r,
            earth_water_aggregator=water_agg,
            earth_impact_catalog=impact_cat,
        )

        catalog_records = []

        # 1. Process Curated High-Priority Sites
        for site in CURATED_EARTH_ANALOG_SITES:
            lat = site["lat"]
            lon = site["lon"]
            try:
                rec = extractor.extract_earth_tile(lat, lon)
                rec["tile_id"] = site["name"]
                rec["analog_category"] = site["category"]
                catalog_records.append(rec)
            except Exception:
                continue

        # 2. Add Systematic Continental Sampling (every 20° lat x 30° lon on land)
        for lat in np.arange(-70.0, 75.0, 20.0):
            for lon in np.arange(-150.0, 160.0, 30.0):
                # Simple land boundary filter (skip deep oceans)
                if abs(lat) < 10.0 and (-150.0 <= lon <= -90.0 or 40.0 <= lon <= 90.0):
                    continue  # Pacific / Indian Ocean
                try:
                    rec = extractor.extract_earth_tile(float(lat), float(lon))
                    rec["tile_id"] = f"Earth_Cell_{lat:+03.0f}N_{lon:+04.0f}E"
                    rec["analog_category"] = "systematic_global_grid"
                    catalog_records.append(rec)
                except Exception:
                    continue

        self._catalog = catalog_records

        # Save to disk
        try:
            with open(self.catalog_file, "w", encoding="utf-8") as f:
                json.dump(catalog_records, f, indent=2)
        except Exception:
            pass

    def get_all_tiles(self) -> List[Dict[str, Any]]:
        """Returns all persistent Earth tiles in the catalog."""
        return self._catalog

    def get_tile_count(self) -> int:
        return len(self._catalog)

    def query_spatial_box(
        self, min_lat: float, max_lat: float, min_lon: float, max_lon: float
    ) -> List[Dict[str, Any]]:
        """Spatial bounding box pushdown filter."""
        res = []
        for t in self._catalog:
            lat = t.get("lat_center", 0.0)
            lon = t.get("lon_center", 0.0)
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                res.append(t)
        return res

    def ingest_dem(self, dem_path: Optional[str] = None) -> int:
        """
        Populates real terrain geomorphometry across all persistent Earth candidate tiles
        from the global Earth DEM without overwriting unrelated fields.
        """
        base_dir = Path(__file__).resolve().parent.parent.parent
        resolved_dem = Path(dem_path) if dem_path else (
            base_dir / "data" / "raw" / "earth" / "dem" / "ETOPO_2022_v1_60s_N90W180_surface.tif"
        )
        if not resolved_dem.exists():
            raise FileNotFoundError(f"Earth DEM file not found at: {resolved_dem}")

        reader = EarthDemReader(resolved_dem)
        reader.open()

        updated_count = 0
        try:
            for t in self._catalog:
                lat_c = t.get("lat_center", 0.0)
                lon_c = t.get("lon_center", 0.0)
                lat_min = t.get("lat_min", lat_c - 0.112)
                lat_max = t.get("lat_max", lat_c + 0.112)
                lon_min = t.get("lon_min", lon_c - 0.112)
                lon_max = t.get("lon_max", lon_c + 0.112)

                half_height = abs(lat_max - lat_min) / 2.0
                half_width = abs(lon_max - lon_min) / 2.0

                elev_m, valid_mask, valid_ratio = reader.read_window_pixels(
                    center_lat=lat_c,
                    center_lon=lon_c,
                    half_width_deg=half_width,
                    half_height_deg=half_height,
                )

                geo_metrics = compute_tile_geomorphometry(
                    elev_m=elev_m,
                    lat_center=lat_c,
                    radius_m=EARTH_VOLUMETRIC_RADIUS_M,
                    pixel_res_deg=1.0 / 60.0,
                    native_res_km=1.853,
                    min_valid_ratio=0.70,
                )

                is_valid = geo_metrics.get("is_valid_coverage", False)
                cov_pct = round(geo_metrics.get("valid_ratio", 0.0) * 100.0, 1)

                t["terrain_valid"] = is_valid
                t["terrain_coverage_pct"] = cov_pct
                t["terrain_mean_elevation_m"] = round(geo_metrics["mean_elevation_m"], 2) if is_valid else None
                t["terrain_std_elevation_m"] = round(geo_metrics["std_elevation_m"], 2) if is_valid else None
                t["terrain_local_relief_m"] = round(geo_metrics["local_relief_m"], 2) if is_valid else None
                t["terrain_mean_slope_deg"] = round(geo_metrics["mean_slope_deg"], 2) if is_valid else None
                t["terrain_max_slope_deg"] = round(geo_metrics["max_slope_deg"], 2) if is_valid else None
                t["terrain_roughness_index_m"] = round(geo_metrics["terrain_roughness_index_m"], 2) if is_valid else None
                t["terrain_hypsometric_integral"] = round(geo_metrics["hypsometric_integral"], 4) if is_valid else None
                t["terrain_hypsometric_skewness"] = round(geo_metrics["hypsometric_skewness"], 4) if is_valid else None
                t["native_res_km"] = 1.853
                t["effective_res_km"] = 1.853
                t["sample_count"] = geo_metrics.get("valid_count", 0)

                # Recompute composite coverage across all evaluated parameter groups
                active_covs = [cov_pct]
                for grp in ["mineral", "thermal", "volatile", "geology"]:
                    grp_cov_key = f"{grp}_coverage_pct"
                    if grp_cov_key in t and t[grp_cov_key] is not None:
                        active_covs.append(t[grp_cov_key])

                t["composite_coverage_pct"] = round(float(np.mean(active_covs)), 1) if active_covs else cov_pct
                updated_count += 1

            # Persist updated catalog to disk
            with open(self.catalog_file, "w", encoding="utf-8") as f:
                json.dump(self._catalog, f, indent=2)

        finally:
            reader.close()

        return updated_count
