# TerraTwin — Milestone 8A: Global Earth DEM Ingestion Report

**Date**: 2026-11-13  
**Status**: Milestone 8A Complete & Verified  
**Test Suite**: 96 / 96 Passing Tests (14 test modules, 100% pass rate)

---

## 1. Executive Summary

Milestone 8A implements global Earth Digital Elevation Model (DEM) ingestion across the TerraTwin platform. Prior to this milestone, Earth candidate tiles had 0% terrain coverage (`terrain_valid: False` for 128 / 128 candidates) because only lunar (LRO LOLA) and Martian (MGS MOLA) DEM rasters had been ingested.

With the ingestion of the authoritative **NOAA NCEI ETOPO 2022 Global Relief Model (60 Arc-Second Surface Elevation)**:
- **100% (128 / 128) of Earth analog candidate tiles** now possess valid, physically verified terrain geomorphometry.
- **Mean terrain coverage** improved from **0.0% to 100.0%**.
- **Mean composite coverage across all evaluated groups** increased from **60.3% to 80.4%**.
- Real physical terrain matching is fully active: Jezero Crater (Mars) and Shackleton Crater (Moon) now compute genuine 5-axis similarity against terrestrial candidates using real slopes, roughness, relief, and hypsometric distributions.

---

## 2. Dataset Selection, Citation & Provenance

### 2.1 Scientific Evaluation of Candidate DEM Sources
| Dataset Candidate | Native Resolution | Global Storage | Licensing / Access | Compatibility Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Copernicus DEM GLO-30** | 1 arc-sec (~30 m) | ~400 GB (compressed) / ~1.5 TB | Open Access (AWS S3) | Exceeds local disk space (24.26 GB free). Severe micro-topographic scale mismatch with planetary sensors (1.9 km Moon, 3.7 km Mars). |
| **Copernicus DEM GLO-90** | 3 arc-sec (~90 m) | ~150 GB | Open Access (AWS S3) | Exceeds single-raster local storage budget. |
| **NOAA ETOPO 2022 (60s)** | **60 arc-sec (~1.85 km)** | **444.38 MB (GeoTIFF)** | **Public Domain (US Gov / NOAA)** | **Selected**. Integrates Copernicus GLO-30, USGS 3DEP, ArcticDEM, and REMA. Scale-commensurate with Moon LOLA (~1.89 km) and Mars MOLA (~3.7 km). Comfortably fits within storage (444 MB). |

### 2.2 Dataset Citation & DOI
- **Source**: National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Information (NCEI).
- **Product**: ETOPO 2022 60 Arc-Second Global Relief Model (Surface Elevation).
- **DOI**: [10.25921/fd45-gt74](https://doi.org/10.25921/fd45-gt74)
- **Reference Standard**: World Geodetic System 1984 (WGS 84), EPSG:9518 (WGS 84 3D / ellipsoidal/orthometric height).
- **Vertical Datum**: Orthometric height in meters relative to the Earth Gravitational Model 2008 (EGM2008) geoid.
- **Integrated Terrestrial Sources**: Copernicus DEM GLO-30 (global continental land surfaces), USGS 3DEP (US & territories), ArcticDEM (high northern latitudes), Reference Elevation Model of Antarctica (REMA), and multi-beam acoustic bathymetry.

---

## 3. Storage, File Architecture & Download Performance

### 3.1 Local Storage Accounting
- **Local Disk Free Space Before Ingestion**: 24.26 GB (on `C:`).
- **Downloaded DEM Raster**: `data/raw/earth/dem/ETOPO_2022_v1_60s_N90W180_surface.tif`
  - Dimensions: 21,600 samples × 10,800 lines (233.28 million cells).
  - Storage Footprint: 465,969,062 bytes (**444.38 MB**).
  - Disk Utilization: ~1.8% of available free disk space.
- **Local Disk Free Space After Ingestion**: 23.81 GB.

### 3.2 Ingestion Architecture & High-Performance Downloader
- Implemented `scripts/download_etopo_parallel.py` utilizing HTTP Range requests (`bytes=start-end`, HTTP 206 Partial Content) with 12 concurrent worker threads and a single file-handle synchronization lock (`threading.Lock`) to prevent Windows OS multi-process file contention (`WinError 32`).
- The 444.38 MB raster was partitioned into 112 4-MB chunks, verified against the NOAA content length, and validated upon completion.

---

## 4. Implementation Details

### 4.1 Memory-Efficient Windowed Reader (`EarthDemReader`)
Located at `src/data_ingestion/earth_dem.py`:
- **Windowed IO**: Uses `rasterio` windowed extraction (`from_bounds`) directly from disk. Avoids loading the full 233.28-million-element global array into RAM.
- **Coordinate Normalization**: Normalizes query longitude from both `[-180°, +180°]` and `[0°, 360°]` into `[-180.0, 180.0]`.
- **Antimeridian Wrapping**: Automatically detects when analysis bounding boxes cross the $\pm 180^\circ$ antimeridian, reads the eastern and western bounding windows independently, and concatenates them horizontally along the meridian seam.
- **Polar Boundary Clamping**: Prevents window bounds from exceeding $[-90^\circ, +90^\circ]$ at the poles.
- **Nodata Quality Masking**: Detects `-99999.0` nodata values and non-finite floats, setting invalid pixels strictly to `NaN` (never converted to zero).

### 4.2 Geomorphometry Derivatives Extraction
Reuses the established `src.core.metrics.compute_tile_geomorphometry` engine:
- **Horn's Spherical Physical Slope**: Computes surface gradients on a sphere of radius $R = 6,371,008.8\text{ m}$ with metric cell increments:
  $$dy = R \cdot \Delta\phi_{\text{rad}}, \quad dx = R \cdot \cos(\phi) \cdot \Delta\lambda_{\text{rad}}$$
- **Terrain Roughness Index (TRI)**: Wilson et al. (2007) standard local relief roughness in meters.
- **Local Relief**: Difference between maximum and minimum valid elevation within the ~25 km tile ($z_{\max} - z_{\min}$).
- **Hypsometric Derivatives**:
  - Hypsometric Integral (HI): $\frac{\bar{z} - z_{\min}}{z_{\max} - z_{\min}}$ (quantifies stage of geomorphic landscape dissection).
  - Hypsometric Skewness: Fisher-Pearson skewness coefficient of valid elevation distribution.
- **Scale Harmonization**:
  - Native Resolution: 60 arc-seconds ($\approx 1.853\text{ km}$ at equator).
  - Effective Resolution: $1.853\text{ km}$, scale-invariant and commensurate with LOLA (1.895 km) and MOLA (3.7 km).

### 4.3 Catalog Upgrader (`EarthCatalogManager.ingest_dem()`)
Located at `src/processing/earth_catalog.py`:
- Populates all 128 candidate records in `data/processed/earth_analog_catalog.json`.
- **Non-destructive Ingestion**: Strictly preserves all non-terrain fields (mineralogy mode, GLiM lithology, MODIS LST thermal metrics, JRC water occurrence, glaciated area fractions, PASS/EID impact structure counts and proximities, crater densities, coordinates, categories, and tile IDs).
- Updates `composite_coverage_pct` dynamically across all active observed parameter groups.

---

## 5. Coverage Improvement Summary

| Metric | Before Milestone 8A | After Milestone 8A | Change |
| :--- | :--- | :--- | :--- |
| **Tiles with Valid Terrain** | 0 / 128 (0.0%) | **128 / 128 (100.0%)** | **+128 tiles (+100.0%)** |
| **Mean Terrain Coverage** | 0.0% | **100.0%** | **+100.0%** |
| **Curated Sites Valid** | 0 / 40 (0.0%) | **40 / 40 (100.0%)** | **+40 sites (+100.0%)** |
| **Global Grid Valid** | 0 / 88 (0.0%) | **88 / 88 (100.0%)** | **+88 sites (+100.0%)** |
| **Mean Composite Coverage** | 60.3% | **80.4%** | **+20.1%** |
| **Minimum Composite Coverage** | 40.0% | **60.0%** | **+20.0%** |

---

## 6. Scientific Validation Across Geomorphic Regimes

Representative sites across deserts, mountains, polar deserts, evaporite basins, and impact structures were tested and verified:

### 6.1 Flat Topography & Low-Relief Playas
- **Salar de Uyuni Evaporite Basin, Bolivia** (World's flattest salt flat, satellite altimeter calibration baseline):
  - Mean Elevation: **3,653.5 m** (Std: **0.0 m**)
  - Local Relief: **0.0 m**
  - Mean Slope: **0.0°** (Max: **0.0°**)
  - TRI: **0.0 m**
  - Hypsometric Integral: **0.5000** (ideal flat plain)
  - Result: Confirms algorithm correctly reports zero roughness and zero slope for flat evaporite basins without numerical noise.
- **Lake Eyre Ephemeral Playa, South Australia**:
  - Mean Elevation: **-15.5 m** (below sea level)
  - Local Relief: **0.0 m**, Mean Slope: **0.0°**

### 6.2 Topographic Depressions Below Sea Level
- **Death Valley / Mojave Desert, USA**:
  - Coordinates: 36.63° N, 242.94° E (116.93° W)
  - Mean Elevation: **224.36 m** (Std: **357.05 m**)
  - Min Elevation in Window: **-83.9 m** (Badwater Basin officially -86 m)
  - Local Relief: **1,760.61 m**
  - Mean Slope: **3.58°** (Max: **12.12°**)
  - TRI: **86.65 m**
  - Hypsometric Integral: **0.1736**, Skewness: **1.7713** (deep incised valley)
- **Danakil Depression Hydrothermal Basin, Ethiopia**:
  - Mean Elevation: **36.82 m**, Relief: **812.87 m**, Slope: **1.79°**

### 6.3 Rugged Alpine & Volcanic Massifs
- **Mount Erebus Anorthoclase Volcano, Ross Island, Antarctica**:
  - Mean Elevation: **1,356.74 m**
  - Local Relief: **3,814.19 m** (Erebus peak 3,794 m rising from sea level)
  - Mean Slope: **10.85°** (steep stratovolcano slopes)
  - TRI: **183.64 m**
- **Altiplano Volcanic Plateau, Chile/Bolivia**:
  - Mean Elevation: **4,975.69 m**, Relief: **1,200.33 m**, Slope: **4.01°**, TRI: **121.81 m**

### 6.4 Polar Deserts & Glaciated Terrain
- **Devon Island / Haughton Crater, Nunavut, Canada** (Mars analog):
  - Mean Elevation: **285.95 m**, Relief: **301.52 m**, Slope: **1.06°**, TRI: **22.57 m**
- **McMurdo Dry Valleys (Taylor Valley), Antarctica**:
  - Mean Elevation: **836.81 m**, Relief: **1,839.76 m**, Slope: **6.85°**, TRI: **142.25 m**
- **St. Elias / Malaspina Glacier, Alaska, USA**:
  - Mean Elevation: **456.34 m**, Relief: **667.82 m**, Slope: **0.83°**, TRI: **17.26 m**

### 6.5 Hypervelocity Impact Structures
- **Sudbury Impact Basin, Ontario, Canada**:
  - Mean Elevation: **285.27 m**, Relief: **150.48 m**, Slope: **0.37°**, TRI: **11.33 m**
  - Geological context preserved: `geology_valid: True`, `earth_impact_structure_present: True`
- **Vredefort Giant Impact Structure, South Africa**:
  - Mean Elevation: **1,426.32 m**, Relief: **202.28 m**, Slope: **0.61°**, TRI: **18.51 m**
- **Lonar Impact Crater in Basalt, India**:
  - Mean Elevation: **546.00 m**, Relief: **118.22 m**, Slope: **0.39°**, TRI: **13.82 m**

---

## 7. Verification of Scientific Safeguards

1. **No Resampling Distortion**:
   - Native grid spacing is 60 arc-seconds ($\approx 1.853\text{ km}$).
   - Recorded as `native_res_km: 1.853` and `effective_res_km: 1.853`.
   - Never presented as high-resolution (e.g. 30 m) topography.
2. **Missing Data Never Treated as Zero**:
   - `nodata` (-99999.0) and non-finite floats are strictly converted to `np.nan`.
   - Where valid ratio $< 70\%$, metrics return `None` / `np.nan`, never `0.0`.
3. **Thresholds & Qualification**:
   - 70% parameter group validity rule enforced.
   - 60% minimum composite coverage threshold strictly respected in `/api/match`.
   - Unobserved groups remain `None` / `N/A` (leaving clean gaps in 5-axis radar profiles).
4. **Preservation of Similarity Algorithms & API Contracts**:
   - All similarity dispersion scales ($\sigma_{\text{slope}} = 3.5^\circ$, $\sigma_{\text{relief}} = 300\text{ m}$, $\sigma_{\text{TRI}} = 35\text{ m}$, etc.) and API response schemas remain unchanged.

---

## 8. Test Suite Verification

A dedicated test module `tests/test_earth_dem.py` was implemented containing 8 comprehensive unit and integration tests.

### Test Execution Results
```
tests/test_earth_dem.py::TestEarthDemReader::test_metadata PASSED                        [ 12%]
tests/test_earth_dem.py::TestEarthDemReader::test_windowed_read_death_valley PASSED     [ 25%]
tests/test_earth_dem.py::TestEarthDemReader::test_longitude_normalization_wrap PASSED   [ 37%]
tests/test_earth_dem.py::TestEarthDemReader::test_antimeridian_crossing PASSED          [ 50%]
tests/test_earth_dem.py::TestEarthDemReader::test_geomorphometry_flat_vs_mountain PASSED [ 62%]
tests/test_earth_dem.py::TestEarthCatalogDEMIngestion::test_catalog_terrain_coverage PASSED [ 75%]
tests/test_earth_dem.py::TestEarthCatalogDEMIngestion::test_preservation_of_unrelated_fields PASSED [ 87%]
tests/test_earth_dem.py::TestEarthCatalogDEMIngestion::test_tile_extractor_with_dem_reader PASSED [100%]
============================== 8 passed in 4.30s ==============================
```

### Full Regression Suite
```
pytest tests/ -q
======================== 96 passed, 1 warning in 12.53s ========================
```
Across all 14 test modules (`test_api`, `test_earth_dem`, `test_metrics`, `test_readers`, `test_real_thermal_extraction`, `test_real_volatiles_geology`, `test_similarity_engine`, `test_thermal_readers`, `test_tile_extractor_5group`, `test_tile_extractor_thermal`, `test_ti_calibration`, `test_ui_phase1`, `test_ui_phase2`, `test_volatiles_geology_synthetic`), **all 96 tests passed with zero failures**.

---

## 9. Remaining Limitations & Next Steps

1. **Remaining Limitations**:
   - ETOPO 2022 60s is a global bathymetric-topographic surface model. In open ocean waters, surface elevation reflects sea level ($0\text{ m}$) or bathymetry; however, TerraTwin filters out open-ocean tiles via `earth_water_aggregator` (`earth_high_occurrence_water_fraction >= 0.80`).
   - Micro-relief features $< 1.8\text{ km}$ across (e.g. narrow impact crater rims like Meteor Crater, diameter 1.2 km) are smoothed within the 60 arc-second grid cell. This behavior is scientifically intentional to maintain scale-parity with Moon LOLA (1.89 km) and Mars MOLA (3.7 km).
2. **Next Steps (Milestone 8B)**:
   - Ingest global binned monthly MODIS Land Surface Temperature (LST) climatology into the 128 Earth candidate tiles to provide diurnal temperature ranges ($\Delta T$) and elevate thermal parameter group coverage.
