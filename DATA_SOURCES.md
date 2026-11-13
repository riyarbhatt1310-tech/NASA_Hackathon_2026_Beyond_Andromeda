# TerraTwin: Multi-Parameter Planetary Data Sources & Scientific Specifications

TerraTwin performs multi-parameter comparative planetary geomorphometry, mineralogy, thermophysics, volatile distribution, and geological contextualization across Earth, the Moon, and Mars.

---

## 1. Core Scientific Rules & Principles

1. **Resolution Integrity & Effective Resolution Tracking**:
   - The common physical analysis scale is $\sim 25\text{ km} \times 25\text{ km}$ ($625\text{ km}^2$).
   - Resampling or aggregating to 25 km **never** implies increased measurement precision.
   - Every feature record explicitly logs:
     - `native_resolution_km`: Original physical pixel/measurement footprint.
     - `effective_resolution_km`: Spatial resolution of the underlying sensor.
     - `valid_sample_count`: Number of native measurements inside the cell.
2. **Body-Specific Geodesy & Equal Physical-Area Gridding**:
   - Every body's analysis grid is constructed using its true mean radius ($R_{\text{Earth}} = 6,371.0\text{ km}$, $R_{\text{Moon}} = 1,737.4\text{ km}$, $R_{\text{Mars}} = 3,396.2\text{ km}$).
   - Longitudinal grid spacing scales with $\cos(\phi)$ so that each cell covers $\approx 625\text{ km}^2$ of physical surface area on that specific planetary body.
3. **No Direct Equivalence of Divergent Mineralogical Proxies**:
   - Lunar UVVIS optical inversions (wt% FeO, wt% TiO2) and Martian thermal emission spectra (modal mineral % from deconvolution) cannot be treated as identical quantities.
   - Shared cross-planetary categories are formed **only** where scientifically justified (e.g. *Mafic Basaltic Affinity Index*, *Felsic/Anorthositic Highland Index*, *Dust/Silt Mantling Mask*).
   - Earth categorical lithology (GLiM) must use categorical mode (majority category) and area fractions within tiles. Never average category IDs.
4. **Contextual Thermophysics**:
   - Surface temperatures are strictly separated into daytime and nighttime observations and tagged with their local solar time (LST), diurnal cycle phase, observation period, and heliocentric distance.
   - Climatological averaging must not blur diurnal extremes.
   - Thermal inertia ($I = \sqrt{k \rho c}$) is used as the primary invariant metric for regolith grain size and bedrock exposure.
5. **Rigorous Volatile Categorization**:
   - TerraTwin explicitly distinguishes:
     - **Actual Liquid Surface Water** (terrestrial lakes, rivers, wetlands).
     - **Permanent Surface Ice & Glaciers** (terrestrial glaciers, polar caps).
     - **Subsurface Hydrogen Proxies** (epithermal neutron suppression, Water-Equivalent Hydrogen wt% in top 1 meter).
     - **Permanently Shadowed Regions (PSRs)** (lunar/polar micro-cold traps capable of cryogenic ice preservation).
6. **Crater Density Standards**:
   - Crater density is computed using consistent physical diameter thresholds:
     - $N(1)$: Cumulative craters $\ge 1\text{ km}$ diameter per $1,000\text{ km}^2$.
     - $N(5)$: Cumulative craters $\ge 5\text{ km}$ diameter per $1,000\text{ km}^2$.
   - Catalogue completeness limits are preserved (e.g. Robbins lunar catalogue is complete to $D \approx 1.5\text{ km}$; Robbins Mars to $D \approx 1.0\text{ km}$).
7. **Quality Accounting & Strict 70% Coverage Rule**:
   - Every parameter maintains a `coverage_ratio` $\in [0.0, 1.0]$.
   - Tiles must meet a minimum valid coverage threshold (default 70%, `min_valid_coverage = 0.70`) for a parameter layer to be considered valid (`parameter_valid = True`).
   - If coverage < 70%, the metric is marked unobserved (`None`). Missing data is NEVER treated as zero or fabricated.

---

## 2. Parameter Matrix Across Earth, Moon, and Mars

| Parameter Group | Earth Dataset | Moon Dataset | Mars Dataset |
| :--- | :--- | :--- | :--- |
| **1. Terrain** | Copernicus DEM GLO-30 2024 (ESA/Airbus via GEE) | NASA LOLA LDEM_16_FLOAT (LRO/MIT) [DOWNLOADED & VERIFIED] | MGS MOLA MEGDR megt90n000eb (NASA PDS) [DOWNLOADED & VERIFIED] |
| **2. Mineralogy** | Global Lithological Map (GLiM v1.0) & S2/L8 Mineral Ratios | Clementine UVVIS FeO & TiO2 Inversion Maps (USGS/PDS) [FeO DOWNLOADED & VERIFIED] | MGS TES Global Mineral Abundances (Bandfield/Christensen) |
| **3. Thermal** | MODIS Terra/Aqua Land Surface Temp (MOD11A1 / MYD11A1) | LRO Diviner Global Products (GDR / GCP) (UCLA/PDS) | 2001 Mars Odyssey THEMIS Global Thermal Inertia & TES LST |
| **4. Water & Ice** | JRC Global Surface Water & NSIDC GLIMS Cryosphere | Lunar Prospector Neutron (LP-NS WEH) & LOLA Polar PSRs | Mars Odyssey GRS/HEND Subsurface Water-Equivalent Hydrogen |
| **5. Geology** | USGS Global Ecosystems / Earth Impact Database / GLiM | USGS Unified Geologic Map of Moon & Robbins Lunar Craters | USGS Geologic Map of Mars (SIM 3292) & Robbins Mars Craters |

---

## 3. Parameter Group Specifications

### Group 1: Terrain Geomorphometry
- **Earth (Copernicus DEM GLO-30 2024)**:
  - Native Resolution: 1.0 arcsec (~30 m at equator).
  - Effective Resolution: ~30 m.
  - Derived Metrics: Spherical Horn slope, roughness (TRI), relief, hypsometric integral and skewness.
- **Moon (NASA LOLA LDEM_16_FLOAT)**:
  - Native Resolution: 16 pix/deg ($\approx 1.895\text{ km/pixel}$ at equator).
  - Effective Resolution: ~1.9 km.
  - File: `data/raw/moon/LDEM_16_FLOAT.IMG` (66,355,200 bytes, float32 LE) [VERIFIED].
- **Mars (MGS MOLA MEGDR megt90n000eb)**:
  - Native Resolution: 16 pix/deg ($\approx 3.704\text{ km/pixel}$ at equator).
  - Effective Resolution: ~3.7 km.
  - File: `data/raw/mars/megt90n000eb.img` (33,177,600 bytes, int16 BE) [VERIFIED].

### Group 2: Mineralogy & Composition
- **Earth (GLiM v1.0 Lithology)**:
  - Native Resolution: Vector polygons (1:1M scale), binned to 0.5° raster.
  - Reader/Aggregator: `EarthGLiMAggregator` (`src/data_ingestion/earth_glim.py`).
  - Aggregation Method: Categorical mode (majority lithological class ID) and area fraction. IDs are never averaged.
- **Moon (Clementine UVVIS FeO & TiO2)**:
  - Native Resolution: 0.5° global grids (~15 km) and 1 km USGS binned mosaics.
  - FeO File: `data/raw/moon/feO_1km.tif` (139,304,752 bytes, float32) [VERIFIED].
  - TiO2 Calibration: Evaluated using published Lucey et al. (2000) algorithm (see validation report below).
- **Mars (MGS TES Surface Mineralogy)**:
  - Native Resolution: 1.0° (~59 km).
  - Derived: Pyroxene, Olivine, Plagioclase modal percentages from thermal emission deconvolution.

### Group 3: Thermophysical Environment

> [!IMPORTANT]
> **Spatial Coverage & Resolution Boundaries**:
> 1. **Moon Diviner Coverage is Regional**: The verified Diviner GCP grids (`diviner_day.tif`, `diviner_night.tif`) cover **only the equatorial latitude band** ($0^\circ\text{ to } 10^\circ\text{ N}$, $-180^\circ\text{ to } +180^\circ\text{ E}$). The high-resolution GHRM GeoTIFF (`diviner_night_ghrm_apollo11.tif`) covers **only the Apollo 11 region** ($512 \times 512$ pixels, ~236 m/pix). These files do **not** provide global lunar thermal coverage across mid-latitudes or poles.
> 2. **Earth MODIS Validation is Regional**: The verified MODIS Aqua L3 files (`modis_lst_day.tif`, `modis_lst_night.tif`) cover **only Tile h08v05** (the Mojave Desert / Death Valley terrestrial analog region, ~$1200 \times 1200\text{ km}$). Global Earth thermal processing requires querying additional tiles or global composites.
> 3. **Mars THEMIS vs. Global TES Distinctions**:
>    - **Mars THEMIS is Regional**: `themis_ti_jezero_100m.tif` is a high-resolution 100 m/pixel regional crop covering **only Jezero Crater** ($50\text{ km} \times 50\text{ km}$).
>    - **Mars TES is Global**: `global_ti_day_2007.img`, `global_ti_night_2007.img`, and `global_ti_msk_night_2007.img` provide **true global coverage** ($3600 \times 7200$ pixels, 20 pix/deg = 2.96 km/pix, Lat $-90^\circ\text{ to }+90^\circ$, Lon $-180^\circ\text{ to }+180^\circ$) with 88.3% global observed nighttime coverage.

- **Moon (LRO Diviner Lunar Radiometer)**:
  - Instrument: Diviner Lunar Radiometer Experiment (LRO).
  - Coverage: **Regional Equatorial Band** ($0^\circ–10^\circ\text{ N}$) and **Regional Apollo 11 Crop**. (Not global).
  - Product: PDS GCP Diurnal Cumulative Climatology (Williams et al. 2017) and GHRM (128 pix/deg) Bolometric Brightness Temperature.
  - Local Solar Time: Midday bolometric temperature (~12:00 LST, 11.5–12.5 h) and midnight bolometric temperature (~00:00 LST, 23.5–0.5 h).
  - Native Resolution: 0.5° (~15 km at equator) and 128 pix/deg (~236 m/pix).
  - Units: Kelvin (K). Equatorial observed range: Midday 371.9–402.6 K (mean 390.2 K), Midnight 95.6–131.4 K (mean 101.5 K). Diurnal swing: ~290 K.
  - Verified Files:
    - `data/raw/moon/thermal/diviner_day.tif` (28.0 KB, 20x720 float32, EPSG:4326, 99.2% valid, Regional 0°–10° N) [DOWNLOADED & VERIFIED]
    - `data/raw/moon/thermal/diviner_night.tif` (31.1 KB, 20x720 float32, EPSG:4326, 99.7% valid, Regional 0°–10° N) [DOWNLOADED & VERIFIED]
    - `data/raw/moon/thermal/diviner_night_ghrm_apollo11.tif` (976.5 KB, 512x512 float32, 128 pix/deg, Regional Apollo 11) [DOWNLOADED & VERIFIED]
  - Reader: `MoonDivinerReader` (`src/data_ingestion/moon_diviner.py`).
  - Status: Fully Operational for Regional Ingestion & Testing.

- **Mars (2001 Mars Odyssey THEMIS & MGS TES)**:
  - THEMIS Thermal Inertia (**Regional**):
    - Instrument: Thermal Emission Imaging System (THEMIS).
    - Coverage: **Regional Jezero Crater Crop** ($50\text{ km} \times 50\text{ km}$). (Not global).
    - Product: USGS Astropedia 32-bit quantitative thermal inertia mosaic (Edwards et al. 2014 / Ferguson et al.).
    - Native Resolution: 100 m/pixel.
    - Units: $\text{J m}^{-2} \text{ K}^{-1} \text{ s}^{-1/2}$ (tiu). Observed Jezero Crater range: 114.4–1916.9 tiu (mean 360.8 tiu, 100% valid coverage).
    - Verified File: `data/raw/mars/thermal/themis_ti_jezero_100m.tif` (1.03 MB, 500x500 float32, LZW, Regional Jezero) [DOWNLOADED & VERIFIED].
    - Reader: `MarsThermisReader` (`src/data_ingestion/mars_thermis.py`).
  - MGS TES Daytime & Nighttime Thermal Inertia & Bolometric Temperature (**Global**):
    - Instrument: MGS Thermal Emission Spectrometer (TES).
    - Coverage: **True Global Coverage** ($3600 \times 7200$, Lat $-90^\circ\text{ to }+90^\circ$, Lon $-180^\circ\text{ to }+180^\circ$).
    - Product: NASA PDS Geosciences `MGS-M-TES-5-TIMAP-V1.0` (Putzig et al. 2007).
    - Orbit/LST: Sun-synchronous, ~14:00 (daytime pass) and ~02:00 (nighttime pass).
    - Native Resolution: 20 pix/deg (~2.96 km/pixel at equator).
    - Units: tiu (thermal inertia) and Kelvin (bolometric temperature).
    - Verified Files:
      - `data/raw/mars/thermal/global_ti_day_2007.img` (51.84 MB, 3600x7200 int16 BE) + `.lbl` [GLOBAL DOWNLOADED & VERIFIED]
      - `data/raw/mars/thermal/global_ti_night_2007.img` (51.84 MB, 3600x7200 int16 BE, 88.3% global coverage) + `.lbl` [GLOBAL DOWNLOADED & VERIFIED]
      - `data/raw/mars/thermal/global_ti_msk_night_2007.img` (25.92 MB, 3600x7200 uint8 interpolation mask) + `.lbl` [GLOBAL DOWNLOADED & VERIFIED]
    - Reader: `MarsTesTempReader` (`src/data_ingestion/mars_tes_temp.py`) via native GDAL PDS driver.
  - Status: Fully Operational (Regional THEMIS 100m + Global MGS TES).

- **Earth (NASA MODIS Terra/Aqua Land Surface Temperature)**:
  - Instrument: Moderate Resolution Imaging Spectroradiometer (MODIS Aqua MYD11A1.061 / Terra MOD11A1.061).
  - Coverage: **Regional Tile h08v05** (Mojave Desert / Death Valley terrestrial analog, ~$1200 \times 1200\text{ km}$). (Not global).
  - Source: NASA LP DAAC via Microsoft Planetary Computer STAC / Cloud-Optimized GeoTIFFs.
  - Nominal Local Solar Time: Aqua ~13:30 LST (Daytime maximum) and ~01:30 LST (Nighttime minimum).
  - Native Resolution: 1 km (1200x1200 Sinusoidal grid).
  - Calibration: Raw uint16 DN $\times 0.02 \to \text{Kelvin}$. QC bitmask validation (bits 0-1 $\le 1$).
  - Terrestrial Analog Observation (Mojave / Death Valley, Tile h08v05, July 16, 2023):
    - Daytime LST: Min 273.30 K, Max 347.80 K, Mean 322.69 K (49.5 °C).
    - Nighttime LST: Min 269.20 K, Max 316.60 K, Mean 294.46 K (21.3 °C).
    - Diurnal Range: ~24.2–28.2 K.
  - Verified Files:
    - `data/raw/earth/thermal/modis_lst_day.tif` (1.59 MB, uint16 Sinusoidal, Regional h08v05) [DOWNLOADED & VERIFIED]
    - `data/raw/earth/thermal/modis_lst_night.tif` (1.51 MB, uint16 Sinusoidal, Regional h08v05) [DOWNLOADED & VERIFIED]
    - `data/raw/earth/thermal/modis_qc_day.tif` (0.30 MB, uint8 Sinusoidal, Regional h08v05) [DOWNLOADED & VERIFIED]
    - `data/raw/earth/thermal/modis_qc_night.tif` (0.19 MB, uint8 Sinusoidal, Regional h08v05) [DOWNLOADED & VERIFIED]
  - Reader: `ModisLSTReader` (`src/data_ingestion/earth_modis.py`).
  - Status: Fully Operational for Regional Analog Ingestion & Testing.
  - MGS TES Temperature:
    - Instrument: Thermal Emission Spectrometer (TES).
    - Product: Daytime (~14:00 LST) and Nighttime (~02:00 LST) Bolometric Surface Temperatures.
    - Native Resolution: 1.0° (~59.3 km at equator). Format: VICAR / GeoTIFF.
    - Units: Kelvin (K). Typical Martian range: 140 K (winter night) to 290 K (summer day).
    - Reader: `MarsTesTempReader` (`src/data_ingestion/mars_tes_temp.py`).
### Group 4: Water, Ice & Volatiles

> [!IMPORTANT]
> **Strict Volatile Discrimination & Proxy Semantics**:
> 1. **Epithermal Neutron Suppression is an Elemental Hydrogen Proxy, NOT Confirmed Water Ice**:
>    - Moon: Lunar Prospector Neutron Spectrometer (LP-NS) epithermal count suppression reflects total elemental hydrogen (converted to Water-Equivalent Hydrogen wt% via Feldman et al. 2001: $\text{WEH wt}\% \approx \text{H (ppm)} \times 8.936 \times 10^{-4}$). Effective spatial resolution is ~43 km FWHM.
>    - Procellarum KREEP Terrane (PKT) Caveat: Elevated Thorium, Samarium, and Gadolinium absorb thermal/epithermal neutrons and can artificially distort hydrogen proxies. Flagged via `is_procellarum_kreep_terrane`.
>    - Mars: 2001 Mars Odyssey GRS (`h2o_sr_5x5.tab` v2.0) epithermal neutron reduction reflects total hydrogen in the top ~1 meter, conflating hydrated minerals (phyllosilicates, sulfates), adsorbed moisture, and ground ice. Effective resolution is ~600 km reflecting 10° boxcar smoothing before 5° rebinning.
> 2. **Permanently Shadowed Regions (PSRs) Do Not Prove Ice**:
>    - Lunar polar cold-trap fractions (`volatile_psr_area_fraction`) identify micro-cryogenic environments ($T < 110\text{ K}$) capable of thermal retention, but do not confirm ice presence or ice thickness. PSR layer is non-blocking and optional.
> 3. **Mars SWIM Ice Consistency Index is NOT an Area Fraction**:
>    - `mars_swim_ice_consistency_index` $\in [-1.0, 1.0]$ is a dimensionless agreement metric across five independent remote-sensing methods (radar dielectric, radar surface, thermal, neutron, geomorphic). It is strictly isolated and NEVER converted to an area fraction.
> 4. **Terrestrial Water vs. Glaciers vs. Deferred Snow/Ice**:
>    - JRC Global Surface Water (GSW v1.5) provides historical water detection occurrence (0–100% of valid cloud-free acquisitions between 1984–2024). A project-defined threshold ($\ge 80\%$) defines persistent open water (`earth_high_occurrence_water_fraction`).
>    - GLIMS / Natural Earth Glaciated Areas (`ne_10m_glaciated_areas.shp`) provides mapped permanent glacier and ice sheet polygon area fraction (`earth_glacier_area_fraction`).
>    - Perennial snow/ice fraction is formally deferred (`earth_perennial_snow_ice_fraction = None`) due to external authentication constraints.

- **Moon (Lunar Prospector Neutron Spectrometer & LOLA PSRs)**:
  - Instrument: Lunar Prospector Neutron Spectrometer (LP-NS) epithermal neutron spectrometer (Feldman et al. 2001 special research product).
  - Effective Resolution: ~43 km FWHM. Grid spacing: 0.5° equal-area sinusoidal bins.
  - Proxy: Water-Equivalent Hydrogen ($\text{WEH wt}\% = \text{H (ppm)} \times 8.936 \times 10^{-4}$).
  - Verified File: `data/raw/moon/volatiles/hydrogenlow.txt` (622.2 KB, 42,940 equal-area grid records) [DOWNLOADED & VERIFIED].
  - Reader: `MoonVolatilesReader` (`src/data_ingestion/moon_volatiles.py`).
- **Mars (2001 Mars Odyssey GRS & SWIM Cryosphere)**:
  - Instrument: 2001 Mars Odyssey Gamma Ray Spectrometer (GRS) epithermal neutron detector (Boynton et al. 2002, 2007).
  - Product: PDS Geosciences `ODY-M-GRS-5-ELEMENTS-V1.0` product `H2O_SR_5X5` (Version 2.0).
  - Effective Resolution: ~600 km reflecting 10° boxcar smoothing over 2° raw data, rebinned at 5° grid spacing.
  - Coverage: Latitudes $-57.5^\circ\text{ to }+57.5^\circ$ (polar seasonal caps excluded). Observed range: 1.65 wt% (Noachis Terra dry) to 7.40 wt% (Medusae Fossae hydrous).
  - Verified File: `data/raw/mars/volatiles/h2o_sr_5x5.tab` (186.6 KB, 2,592 records) + `h2o_sr_5x5.lbl` [DOWNLOADED & VERIFIED].
  - Reader: `MarsVolatilesReader` (`src/data_ingestion/mars_volatiles.py`).
- **Earth (JRC Global Surface Water & Natural Earth Glaciers)**:
  - Products: EC JRC GSW v1.5 (Landsat 5/7/8/9, 30 m resolution) and Natural Earth / GLIMS glaciated polygon inventory (`ne_10m_glaciated_areas.shp`).
  - Native Resolution: 30 m (JRC) and 1:10M vector polygons (Glaciers).
  - Verified File: `data/raw/earth/volatiles/glaciers/ne_10m_glaciated_areas.shp` (3.94 MB, 1,886 glacier polygons) [DOWNLOADED & VERIFIED].
  - Reader: `EarthWaterAggregator` (`src/data_ingestion/earth_water.py`).

---

### Group 5: Geological Context & Landforms

> [!IMPORTANT]
> **Planetary Crater Chronometry vs. Terrestrial Impact Structures**:
> 1. **Harmonized Crater Chronometry on Moon and Mars**:
>    - Uses official Robbins catalogs: Moon Robbins et al. (2014) and Mars Robbins & Hynek (2012).
>    - Stores compact crater IDs and summary statistics (min, max, median, mean diameter) rather than unbounded coordinate arrays.
>    - Cumulative crater densities $N(1)$ and $N(5)$ per $1,000\text{ km}^2$.
>    - Poisson counting uncertainty propagated: $\sigma_{N} = \frac{\sqrt{N}}{\text{Area}} \times 1000$.
>    - Small-count statistical limitation flag: `low_count_uncertainty = True` when $N < 5$.
> 2. **Terrestrial Impact Structures are Discrete Morphological Features, NOT Crater Chronometry**:
>    - Earth's dynamic crust (plate tectonics, fluvial/glacial erosion, sedimentation) destroys impact landforms over geologic time.
>    - Earth crater density $N(1)$ is **strictly prohibited** (`None`).
>    - Preserves Planetary and Space Science Centre (PASSC) Earth Impact Database (EID) confirmed structures, structure names, and distance to nearest confirmed structure (`earth_impact_structure_proximity_km`).
> 3. **Geologic Units**:
>    - Moon: USGS Unified Geologic Map of the Moon (1:5M scale; Fortezzo et al. 2020) stratigraphic units (Pre-Nectarian, Nectarian, Imbrian, Eratosthenian, Copernican).
>    - Mars: USGS Global Geologic Map of Mars (SIM 3292, 1:20M scale; Tanaka et al. 2014) chronostratigraphic epochs (Noachian, Hesperian, Amazonian).
>    - Isolated as descriptive exploratory context metadata; categorical epoch labels are not conflated into continuous numerical distance metrics.

- **Moon Crater Catalog (Robbins Lunar 2014)**:
  - Verified File: `data/raw/moon/geology/robbins_lunar_craters.csv` [DOWNLOADED & VERIFIED].
  - Reader: `PlanetaryCraterCatalog("moon")` (`src/data_ingestion/crater_catalog.py`).
- **Mars Crater Catalog (Robbins Mars 2012)**:
  - Verified File: `data/raw/mars/geology/robbins_mars_craters.csv` [DOWNLOADED & VERIFIED].
  - Reader: `PlanetaryCraterCatalog("mars")` (`src/data_ingestion/crater_catalog.py`).
- **Earth Impact Database (PASSC EID)**:
  - Verified File: `data/raw/earth/geology/earth_impact_database.geojson` [DOWNLOADED & VERIFIED].
  - Reader: `EarthImpactCatalog` (`src/data_ingestion/earth_impacts.py`).
- **Geologic Units Aggregator**:
  - Module: `GeologicUnitAggregator` (`src/data_ingestion/geologic_units.py`).

---

## 4. Moon TiO₂ Calibration Validation Report

### Background
During Milestone 3 and earlier discussions, two approaches for deriving lunar TiO₂ from Clementine UVVIS data were proposed:
1. A legacy linear shortcut: $\text{TiO}_2 = 30.0 \times R - 5.0$, where $R$ was assumed to be the red channel ($750\text{ nm} / 415\text{ nm}$ ratio).
2. A trial polynomial with parameters $x_0 = 0.23, y_0 = 0.05, a_0 = -0.0135, a_1 = 1.03, a_2 = 0.0$.

### Peer-Reviewed Literature Verification
The published source paper was inspected:
> **Lucey, P. G., Blewett, D. T., & Jolliff, B. L. (2000).** *Lunar iron and titanium abundance algorithms based on final processing of Clementine ultraviolet-visible images.* Journal of Geophysical Research: Planets, 105(E8), 20297–20305.

The exact mathematical formulation from Lucey et al. (2000) is:
$$\theta_{\text{Ti}} = \arctan \left[ \frac{(R_{415} / R_{750}) - y_{0\text{Ti}}}{R_{750} - x_{0\text{Ti}}} \right]$$
where the origin point is:
$$(x_{0\text{Ti}}, y_{0\text{Ti}}) = (0.00, 0.42)$$
and the abundance equation calibrated against Apollo and Luna soil samples is:
$$\text{wt}\% \text{ TiO}_2 = 3.708 \times (\theta_{\text{Ti}})^{5.979}$$

### Validation Findings
1. **Mathematical divergence**: The legacy linear shortcut diverges by more than $5\text{ wt}\%$ RMSE across typical lunar mare and highland soils. It severely underestimates high-Ti basalts (such as Apollo 11 and Apollo 17 mare soils) and generates negative values or spurious artifacts over highland terrains.
2. **Exact Mathematical Specification & Verification**:
   - The angle $\theta_{\text{Ti}}$ is computed strictly in **radians** using `np.arctan`.
   - Exact parentheses:
     $$\theta_{\text{Ti}} = \arctan\left( \frac{(R_{415} / R_{750}) - 0.42}{R_{750} - 0.00} \right)$$
   - Abundance equation:
     $$\text{wt}\% \text{ TiO}_2 = 3.708 \times (\theta_{\text{Ti}})^{5.979}$$
   - **Absolute Reflectance Requirement**: The formula fundamentally depends on **both** the color ratio $(R_{415}/R_{750})$ in the numerator AND the **calibrated absolute $750\text{ nm}$ reflectance** $R_{750} \in [0.01, 0.80]$ in the denominator. The color ratio alone is mathematically insufficient.
3. **Strict Policy on Unavailable / Incompatible Inputs**:
   - If an input file lacks calibrated absolute $R_{750}$ reflectance (e.g. provides only false-color ratio bands without absolute reflectance), `MoonTiO2Extractor` and `validate_tio2_calibration` **strictly mark $\text{TiO}_2$ as UNAVAILABLE** (`np.nan`, `mask = False`, `None` in tile records).
   - TerraTwin **never** falls back to uncalibrated linear shortcuts or fabricated values.
4. **Data provenance & limitation**: The raw Clementine UVVIS 200 m 3-band mosaic (`uvvis_200m.tif`) is not present in the local repository; attempting to convert raw unverified bands without flat-field calibration introduces significant uncertainty. For science-grade analog matching, TerraTwin requires either the authoritative pre-calibrated USGS product (`Lunar_Clementine_UVVIS_TiO2_ClrBinned_70S70N_1km.tif`) or explicit flagging as `UNAVAILABLE` when raw band reflectance is unverified. Missing data is never zero-filled.

---

## 6. Milestone 6: Global Earth Candidate Catalog & REST API

### Global Earth Analog Candidate Catalog (`data/processed/earth_analog_catalog.json`)
- **Tile Count**: 128 persistent global candidate Earth tiles.
- **Spatial Coverage**:
  - *Curated planetary analog testbeds*: Hyper-arid deserts (Atacama, Mojave, Sahara, Namib, McMurdo Dry Valleys), basaltic volcanic terrains (Hawaii Volcanoes, Iceland volcanic plains, Deccan Traps), arctic cryospheric/polar desert sites (Ellesmere Island, Devon Island, Svalbard, Greenland Ice Sheet, Antarctic Plateau), and terrestrial hypervelocity impact structures (Sudbury Basin, Manicouagan Reservoir, Vredefort Dome, Chicxulub, Ries Crater, Haughton Crater).
  - *Systematic global grid*: Sampled across diverse continental geomorphic provinces to ensure genuine global top-K candidate discovery rather than isolated sample points.
- **Memory Efficiency**: Serialized to structured JSON (544 KB) with zero memory bloat during matching operations.

### Glacier and Water Distinction Policy
- **Natural Earth 10m Glaciated Areas** (`ne_10m_glaciated_areas.shp`):
  - Generalized regional polygon boundaries derived from cartographic scale.
  - Reported strictly under the parameter key: `earth_glaciated_area_fraction`.
- **GLIMS / Randolph Glacier Inventory (RGI 6.0)**:
  - Precise individual glacier outlines with hypsometry and inventory IDs.
  - Reserved strictly for high-resolution glacier inventory extraction under: `earth_glacier_area_fraction`.

### Mandatory Scientific Disclaimers
Every API response and user dashboard view includes the scientific warning:
> *"TerraTwin evaluates quantitative multi-parameter similarity across planetary observation datasets. A high similarity score indicates overlapping physical, mineralogical, or geomorphic metrics in the compared parameters. It does NOT imply geological identity, shared genesis, identical environmental conditions, or human habitability. Extreme differences in atmospheric pressure, volatile state, solar irradiance, and radiation environment must be taken into account when interpreting planetary analog matches."*
