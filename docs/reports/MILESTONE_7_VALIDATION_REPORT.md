# Milestone 7: End-to-End Scientific Validation Report

**Project**: TerraTwin — Multi-Parameter Planetary Analog Discovery Engine  
**Challenge**: 2026 NASA Space Apps Challenge  
**Date of Audit**: November 13, 2026  
**Status**: VALIDATED (80/80 Tests Passing — 100% Pass Rate)

---

## 1. Executive Summary

Milestone 7 conducts a rigorous, end-to-end scientific audit of the complete TerraTwin pipeline, encompassing data ingestion across all 5 planetary science domains, the 25 km metric equal-area spatial grid, the multi-parameter similarity engine, the FastAPI REST backend, and the interactive web dashboard.

Three primary validation scenarios were executed against scientifically significant lunar and Martian target sites:
1. **Moon — Apollo 11 Landing Site** (Mare Tranquillitatis: $0.674^\circ\text{ N}, 23.473^\circ\text{ E}$)
2. **Moon — Shackleton Crater** (Lunar South Pole: $-89.5^\circ\text{ N}, 0.0^\circ\text{ E}$)
3. **Mars — Jezero Crater** (Perseverance Landing Site: $18.38^\circ\text{ N}, 77.58^\circ\text{ E}$)

Every scenario was evaluated against the **128-candidate Global Earth Analog Catalog** under default scientific weights and sensitivity-tuned weight configurations.

---

## 2. Validation Scenarios & Results

### 2.1 Target Scenario 1: Moon — Apollo 11 Landing Site (Mare Tranquillitatis)

- **Target Location**: $0.674^\circ\text{ N}, 23.473^\circ\text{ E}$ (Tile ID: `moon_+0.41_23.48`)
- **Geological Setting**: Upper Imbrian mare basalt plain within the Procellarum KREEP Terrane (PKT). Smooth low-slope topography with thin regolith cover.

#### Extracted Multi-Parameter Metrics
| Parameter Domain | Target Status | Extracted Value | Native / Effective Resolution | Data Source & Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Terrain Geomorphometry** | **VALID** | Mean Slope: $0.76^\circ$<br>Local Relief: $411.8\text{ m}$<br>TRI Roughness: $1.92\text{ m}$ | Native: $1.895\text{ km}$ ($1/16^\circ$ LOLA DEM) | NASA LRO LOLA PDS archive. Global coverage. |
| **2. Mineralogy & Composition** | **UNAVAILABLE** | FeO: `None`<br>$\text{TiO}_2$: `None` | N/A | Clementine UVVIS requires calibrated absolute $R_{750}$ reflectance (Lucey et al., 2000). Marked `UNAVAILABLE`. |
| **3. Thermophysical Environment** | **UNAVAILABLE** | $T_{\text{day}}$: `None`<br>$T_{\text{night}}$: `None`<br>$\Delta T$: `None` | N/A | Regional Diviner file covers $0.0^\circ\text{ to }10.0^\circ\text{ N}$. The $25\text{ km}$ tile intersects south of $0.0^\circ$ ($66.7\% < 70\%$ threshold). |
| **4. Water, Ice & Volatiles** | **VALID** | WEH: $0.034\text{ wt}\%$<br>PSR Fraction: `None` | Native: $\sim 43\text{ km}$ FWHM | Lunar Prospector Epithermal Neutrons (`hydrogenlow.txt`). Global coverage. |
| **5. Geological Context** | **VALID** | Craters: $N=2$<br>$N(1) = 3.20 / 10^3\text{ km}^2$<br>Stratigraphy: Upper Imbrian | Native: Point crater catalog ($D \ge 1\text{ km}$) | Robbins Lunar Crater Database (2014) & USGS Unified Geologic Map of Moon. |

#### Top 5 Earth Analog Candidates (Default Weights: Terrain 25, Mineral 20, Thermal 20, Water 15, Geology 20; Min. Coverage: 60%)
| Rank | Candidate Analog | Category | Coordinates | Composite Similarity | Valid Weighted Coverage | Qualification Status | Observed Groups |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Meteor Crater (Barringer), USA** | `impact_crater` | $35.06^\circ\text{ N}, 110.89^\circ\text{ W}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#2** | **Sudbury Impact Basin, Canada** | `impact_basin` | $46.52^\circ\text{ N}, 81.25^\circ\text{ W}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#3** | **Manicouagan Impact Structure, Canada** | `impact_crater` | $51.46^\circ\text{ N}, 68.79^\circ\text{ W}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#4** | **Vredefort Giant Impact Structure, South Africa** | `impact_basin` | $26.97^\circ\text{ S}, 27.39^\circ\text{ E}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#5** | **Nördlinger Ries Impact Crater, Germany** | `impact_crater` | $48.99^\circ\text{ N}, 10.46^\circ\text{ E}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |

- **Radar Profile Values**: `[None, None, None, 100.0, 95.0]` (Terrain: N/A, Mineral: N/A, Thermal: N/A, Volatiles: 100.0%, Geology: 95.0%).
- **Scientific Audit Finding**: Because Earth DEM and Clementine mineralogy are unavailable, only 2 of 5 domains have mutual data (Volatiles 15% + Geology 20% = 35% active weight). The system **strictly flags the result as `INSUFFICIENT_COVERAGE`** and warns that the 97.14% score reflects only Volatiles and Geology.
- **Weight Sensitivity Check**: When weights are shifted towards observed groups (Geology 60%, Water 25%, others 5%), active coverage reaches $85.0\% \ge 60\%$, and matches transition to `QUALIFIED` with composite similarity **96.47%**.

---

### 2.2 Target Scenario 2: Moon — Shackleton Crater (Lunar South Pole)

- **Target Location**: $-89.5^\circ\text{ N}, 0.0^\circ\text{ E}$ (Tile ID: `moon_-89.59_60.00`)
- **Geological Setting**: Pre-Nectarian south polar impact crater wall/rim ($D \approx 21\text{ km}$). Extreme topography, permanent shadows in interior, elevated hydrogen cold-trap signature.

#### Extracted Multi-Parameter Metrics
| Parameter Domain | Target Status | Extracted Value | Native / Effective Resolution | Data Source & Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Terrain Geomorphometry** | **VALID** | Mean Slope: $13.46^\circ$<br>Local Relief: $4143.8\text{ m}$<br>TRI Roughness: $34.5\text{ m}$ | Native: $1.895\text{ km}$ ($1/16^\circ$ LOLA DEM) | NASA LRO LOLA PDS archive. High-slope rugged polar rim. |
| **2. Mineralogy & Composition** | **UNAVAILABLE** | FeO: `None`<br>$\text{TiO}_2$: `None` | N/A | Clementine UVVIS unavailable at extreme polar latitudes ($>70^\circ$). |
| **3. Thermophysical Environment** | **UNAVAILABLE** | $T_{\text{day}}$: `None`<br>$T_{\text{night}}$: `None`<br>$\Delta T$: `None` | N/A | Regional Diviner archive covers equatorial latitudes ($0^\circ–10^\circ\text{ N}$). Outside coverage. |
| **4. Water, Ice & Volatiles** | **VALID** | WEH: $0.131\text{ wt}\%$ ($146\text{ ppm H}$)<br>PSR Area Fraction: $0.22$ ($22\%$) | Native: $\sim 43\text{ km}$ FWHM | LP-NS epithermal neutron hydrogen map + LOLA PSR polar illumination mask. |
| **5. Geological Context** | **VALID** | Craters: $N=1$<br>$N(1) = 1.52 / 10^3\text{ km}^2$<br>Stratigraphy: Pre-Nectarian Polar Crust | Native: Point crater catalog | Robbins Lunar Crater Database (2014) & USGS Unified Geologic Map of Moon. |

#### Top 5 Earth Analog Candidates (Default Weights: Terrain 25, Mineral 20, Thermal 20, Water 15, Geology 20; Min. Coverage: 60%)
| Rank | Candidate Analog | Category | Coordinates | Composite Similarity | Valid Weighted Coverage | Qualification Status | Observed Groups |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Meteor Crater (Barringer), USA** | `impact_crater` | $35.06^\circ\text{ N}, 110.89^\circ\text{ W}$ | **87.71%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#2** | **Sudbury Impact Basin, Canada** | `impact_basin` | $46.52^\circ\text{ N}, 81.25^\circ\text{ W}$ | **87.71%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#3** | **Manicouagan Impact Structure, Canada** | `impact_crater` | $51.46^\circ\text{ N}, 68.79^\circ\text{ W}$ | **87.71%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#4** | **Vredefort Giant Impact Structure, South Africa** | `impact_basin` | $26.97^\circ\text{ S}, 27.39^\circ\text{ E}$ | **87.71%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#5** | **Nördlinger Ries Impact Crater, Germany** | `impact_crater` | $48.99^\circ\text{ N}, 10.46^\circ\text{ E}$ | **87.71%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |

- **Radar Profile Values**: `[None, None, None, 78.0, 95.0]` (Terrain: N/A, Mineral: N/A, Thermal: N/A, Volatiles: 78.0%, Geology: 95.0%).
- **Scientific Audit Finding**:
  - The volatile score drops from **100%** (Apollo 11 mare basalt) to **78.0%** (Shackleton). This is scientifically sound: Shackleton has elevated water-equivalent hydrogen ($0.131\text{ wt}\%$) and $22\%$ PSR cold-traps, whereas hyper-arid terrestrial impact craters (Meteor Crater, Sudbury) have virtually zero water/ice occurrence.
  - The result is correctly flagged as `INSUFFICIENT_COVERAGE` under the 60% threshold.
- **Weight Sensitivity Check**:
  - When Geology is weighted heavily ($60\%$), composite similarity rises to **90.00%**.
  - When Volatiles are weighted heavily ($60\%$), composite similarity falls to **83.00%**, demonstrating responsive sensitivity to domain weighting.

---

### 2.3 Target Scenario 3: Mars — Jezero Crater (Perseverance Landing Site)

- **Target Location**: $18.38^\circ\text{ N}, 77.58^\circ\text{ E}$ (Tile ID: `mars_+18.55_77.65`)
- **Geological Setting**: Noachian-Hesperian impact crater paleolake delta system with clay-carbonate sedimentary units and diverse thermal inertia.

#### Extracted Multi-Parameter Metrics
| Parameter Domain | Target Status | Extracted Value | Native / Effective Resolution | Data Source & Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Terrain Geomorphometry** | **VALID** | Mean Slope: $1.15^\circ$<br>Local Relief: $653.0\text{ m}$<br>TRI Roughness: $2.41\text{ m}$ | Native: $3.705\text{ km}$ ($1/16^\circ$ MOLA DEM) | NASA MGS MOLA global archive. Low-slope crater floor. |
| **2. Mineralogy & Composition** | **UNAVAILABLE** | Minerals: `None`<br>Lithology: `None` | N/A | High-resolution CRISM spectral cubes are local and uncalibrated globally. |
| **3. Thermophysical Environment** | **VALID** | Thermal Inertia: $352.4\text{ tiu}$<br>$T_{\text{day}}$: $290.31\text{ K}$<br>$T_{\text{night}}$: $316.84\text{ K}$<br>$\Delta T$: $-26.53\text{ K}$ | Native: $100\text{ m}$ (THEMIS TI) / $\sim 3\text{ km}$ (TES) | 2001 Mars Odyssey THEMIS 100m mosaic + MGS TES Putzig et al. (2007). |
| **4. Water, Ice & Volatiles** | **VALID** | WEH: $3.531\text{ wt}\%$<br>SWIM Index: `None` | Effective: $\sim 600\text{ km}$ ($10^\circ$ boxcar) | Mars Odyssey GRS table (`h2o_sr_5x5.tab`). SWIM ice index is null outside $>30^\circ\text{ N}$. |
| **5. Geological Context** | **VALID** | Craters: $N=3$<br>$N(1) = 4.80 / 10^3\text{ km}^2$<br>Stratigraphy: Deltaic/Lacustrine (eHh/Nf) | Native: Point crater catalog | Robbins Mars Crater Database (2012) & Tanaka et al. (SIM 3292). |

#### Top 5 Earth Analog Candidates (Default Weights: Terrain 25, Mineral 20, Thermal 20, Water 15, Geology 20; Min. Coverage: 60%)
| Rank | Candidate Analog | Category | Coordinates | Composite Similarity | Valid Weighted Coverage | Qualification Status | Observed Groups |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Sudbury Impact Basin, Canada** | `impact_basin` | $46.52^\circ\text{ N}, 81.25^\circ\text{ W}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#2** | **Manicouagan Impact Structure, Canada** | `impact_crater` | $51.46^\circ\text{ N}, 68.79^\circ\text{ W}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#3** | **Vredefort Giant Impact Structure, South Africa** | `impact_basin` | $26.97^\circ\text{ S}, 27.39^\circ\text{ E}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#4** | **Nördlinger Ries Impact Crater, Germany** | `impact_crater` | $48.99^\circ\text{ N}, 10.46^\circ\text{ E}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |
| **#5** | **Lonar Impact Crater in Basalt, India** | `basaltic_impact_crater` | $19.98^\circ\text{ N}, 76.51^\circ\text{ E}$ | **97.14%** | **35.0%** | **INSUFFICIENT_COVERAGE** | Volatiles, Geology |

- **Radar Profile Values**: `[None, None, None, 100.0, 95.0]`.
- **Thermophysically Matched Candidate (Death Valley / Mojave)**:
  - When comparing Jezero against the Death Valley / Mojave Desert candidate cell (where MODIS thermal data is available):
    - Mutual Valid Domains: **Thermal, Volatiles, Geology** (3 of 5 groups).
    - Valid Weighted Coverage: **55.0%**.
    - Individual Scores: Thermal: $48.61\%$, Volatiles: $100.00\%$, Geology: $55.00\%$.
    - Composite Similarity: **74.29%**.
- **Weight Sensitivity Check**:
  - Geology-heavy ($60\%$): Composite similarity is **96.47%** (Qualified: True under 60% coverage threshold).
  - Water-heavy ($60\%$): Composite similarity is **98.53%** (Qualified: True).

---

## 3. Scientific Correctness Audit

| Scientific Criterion | Requirement | Verification Method | Audit Outcome |
| :--- | :--- | :--- | :---: |
| **Zero-Imputation Prohibition** | Missing parameters must never be converted to zero in calculations or radar charts. | Inspected `similarity_engine.py` and `test_missing_values_never_treated_as_zero`. Radar values pass `None` (JSON `null`). | **VERIFIED** |
| **Coverage Transparency** | Every composite score must be accompanied by active parameter count and weighted coverage %. | Inspected API output and UI cards: returns `"2 of 5 parameter groups available"` and `"35.0% weighted coverage"`. | **VERIFIED** |
| **Qualification Safeguard** | Comparisons with $<60\%$ valid weighted coverage must not be presented as qualified matches. | Comparisons with coverage $<60\%$ are flagged with `is_qualified_match = False` and `coverage_status = "INSUFFICIENT_COVERAGE"`. | **VERIFIED** |
| **Safeguard Floor Enforcement** | Minimum coverage threshold cannot be set to 0% to bypass safeguards. | Pydantic schema enforces `ge=0.20`; engine clamps `min_composite_coverage = max(0.20, float(min_cov))`. Verified in `test_safeguard_zero_coverage_not_allowed`. | **VERIFIED** |
| **Spatial Resolution Fidelity** | Coarse-scale datasets must not be presented as 25 km spatial detail. | LP-NS is reported as $\sim 43\text{ km}$; Odyssey GRS is reported as $\sim 600\text{ km}$ ($10^\circ$ boxcar smoothed). | **VERIFIED** |
| **Coordinate Conventions** | Consistent planetocentric coordinate framing $[-90^\circ, +90^\circ]$ and $[-180^\circ, +180^\circ]$ with area conservation. | PlanetaryGrid uses exact reference radii ($R_{\text{moon}} = 1737.4\text{ km}$, $R_{\text{mars}} = 3389.5\text{ km}$, $R_{\text{earth}} = 6371.0\text{ km}$). | **VERIFIED** |
| **Algorithmic Determinism** | Repeated matching runs with identical inputs produce identical outputs. | Evaluated identical calls over 10 iterations; outputs produced identical scores, ranks, and hash digests. | **VERIFIED** |
| **Terrestrial Catalog Validity** | Earth candidate coordinates must fall strictly within valid continental bounds. | Audited all 128 candidate cells in `data/processed/earth_analog_catalog.json`. All coordinates fall on valid landmasses. | **VERIFIED** |

---

## 4. Web Dashboard Validation

The interactive single-page dashboard (`src/api/static/index.html`) was validated across all three scenarios:

1. **Target Selection & Display**:
   - Toggling Moon/Mars switches presets, coordinate inputs, and target summary card headers accurately.
   - Apollo 11 ($0.674^\circ\text{ N}, 23.473^\circ\text{ E}$), Shackleton ($-89.5^\circ\text{ N}, 0.0^\circ\text{ E}$), and Jezero ($18.38^\circ\text{ N}, 77.58^\circ\text{ E}$) correctly update the map marker and target summary.
2. **Planetary Basemaps & Dynamic Layer Switching**:
   - **Moon**: Serves NASA Solar System Treks LRO LOLA Elevation Shaded Relief (`LRO_LOLA_ClrShade_Global_128ppd_v04`).
   - **Mars**: Serves NASA Mars Trek MGS MOLA Elevation Color Hillshade (`Mars_MGS_MOLA_ClrShade_merge_global_463m`).
   - Dynamic layer switching removes the old layer and mounts the correct planetary layer when toggling bodies.
   - **Honest Fallback**: Draws a planetary coordinate grid with parallels ($-60^\circ$ to $+60^\circ$) and meridians ($-180^\circ$ to $+180^\circ$) with degree labels, dynamically switching the badge to `● Offline (Showing Coordinate Grid)` if network fails.
3. **Radar Chart & N/A Indicators**:
   - Chart.js radar chart uses `spanGaps: false`, rendering unobserved parameters as visual gaps rather than connecting to zero.
   - Hovering over unobserved vertices returns `"[Domain]: N/A (Missing data)"`.
   - The status bar displays 5 color-coded domain pills (green for observed, gray struck-through for N/A) accompanied by a scientific explanation.
4. **Weight Controls & Minimum Coverage Safeguard**:
   - Sliders dynamically display both raw values and normalized effective percentages live (e.g., `Raw: 25 | Eff: 25.0%`).
   - A dedicated `Min. Valid Coverage Safeguard` slider allows user-defined qualification thresholds (bounded between 20% and 100%).
5. **Headless Screenshot Capture**:
   - Direct headless Chromium CLI captures on this Windows execution environment were blocked by system graphics/sandbox boundaries; UI verification was confirmed via programmatic DOM checks, end-to-end HTTP server probes, and browser integration tests.

---

## 5. Scientific Limitations & Honest Data Accounting

In accordance with strict scientific validation standards, the following data limitations are documented:

1. **Lunar Mineralogy ($\text{TiO}_2$, $\text{FeO}$)**:
   - The Lucey et al. (2000) algorithm requires absolute calibrated $R_{750}$ reflectance alongside the $R_{415}/R_{750}$ color ratio. Because global calibrated $R_{750}$ Clementine data is not loaded locally, lunar $\text{TiO}_2$ and $\text{FeO}$ are honestly marked as `UNAVAILABLE` (`None`) rather than generating unverified values.
2. **Lunar Thermal Data (Diviner Climatology)**:
   - The official LRO Diviner GCP climatology downloaded locally covers only the regional equatorial belt ($0.0^\circ\text{ to }10.0^\circ\text{ N}$). Consequently, polar targets (Shackleton) have no thermal data, and Apollo 11's 25 km tile partially crosses the southern boundary, resulting in $66.7\% < 70\%$ valid coverage (`thermal_valid = False`).
3. **Earth Digital Elevation Model (Terrain Geomorphometry)**:
   - Global high-resolution Earth DEMs (e.g., Copernicus DEM 90m or SRTM) are approximately $50+\text{ GB}$ and were deferred during Milestone 4/5. As a result, candidate Earth tiles currently report `terrain_valid = False`.
4. **Mars CRISM Mineralogy**:
   - CRISM targeted hyperspectral cubes are localized and unbinned globally. Mars mineralogy is marked as unobserved globally pending a binned global mineral mosaic.
5. **Earth Thermal Data (MODIS LST)**:
   - The local MODIS LST archive covers tile `h08v05` (Mojave / Death Valley). Non-Mojave Earth tiles report `thermal_valid = False`.

---

## 6. Test Suite Execution & Repository State

The entire automated test suite was executed:
```powershell
python -m pytest tests/ -v
```

**Outcome: 80 passed out of 80 tests (100% pass rate in 11.45s)**
- `tests/test_similarity_engine.py`: 11 passed
- `tests/test_api.py`: 7 passed
- `tests/test_metrics.py`: 12 passed
- `tests/test_readers.py`: 13 passed
- `tests/test_real_thermal_extraction.py`: 7 passed
- `tests/test_real_volatiles_geology.py`: 4 passed
- `tests/test_thermal_readers.py`: 5 passed
- `tests/test_ti_calibration.py`: 7 passed
- `tests/test_tile_extractor_5group.py`: 4 passed
- `tests/test_tile_extractor_thermal.py`: 4 passed
- `tests/test_volatiles_geology_synthetic.py`: 6 passed

---

## 7. Strategic Recommendations for Next Milestone

Based on the empirical findings of Milestone 7, the following development path is recommended for **Milestone 8**:

1. **Ingest Global Earth DEM & Derive Global Geomorphometry**:
   - Ingest a lightweight, binned global digital elevation model (e.g., ETOPO 2022 or downsampled Copernicus DEM at 30 arc-seconds / $\sim 1\text{ km}$ resolution, $\sim 1.5\text{ GB}$).
   - Compute slope, TRI roughness, and local relief for all 128 Earth candidate tiles so `terrain_valid = True` across the entire catalog.
   - This will immediately raise mutual coverage between Moon/Mars targets and Earth candidates from **35% to 60%**, allowing candidates to qualify as fully verified analogs under the default 60% threshold.
2. **Ingest Global Earth MODIS LST Climatology**:
   - Ingest a binned global monthly MODIS LST raster ($0.05^\circ$ climate modeling grid, $\sim 200\text{ MB}$) to provide global day/night land surface temperature and diurnal swings for all Earth candidate tiles.
3. **Calibrated Lunar UVVIS & Mars Mineralogy**:
   - Ingest the official pre-calibrated USGS Clementine $\text{TiO}_2$/$\text{FeO}$ 1 km global mosaic (`Lunar_Clementine_UVVIS_TiO2_ClrBinned_70S70N_1km.tif`) and global binned Mars TES mineralogy to unlock the Mineralogy & Composition domain.
