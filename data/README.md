# TerraTwin Scientific Data Repository

This directory contains the multi-mission planetary remote-sensing datasets, processed feature layers, and characterized terrestrial analog catalogs powering **TerraTwin**.

---

## Directory Architecture

```text
data/
├── raw/                              # Original downloaded raster & vector datasets (git-ignored)
│   ├── earth/                        # Earth reference datasets
│   │   ├── dem/                      # Copernicus / ETOPO global elevation GeoTIFFs
│   │   ├── geology/                  # Earth Impact Database (PASSC) GeoJSON
│   │   ├── mineralogy/               # GLiM global high-resolution lithology
│   │   ├── thermal/                  # MODIS MOD11C3 day/night land surface temperature
│   │   └── volatiles/                # HydroSHEDS / JRC global water / glacier fraction
│   ├── mars/                         # Mars orbital datasets
│   │   ├── dem/                      # MGS MOLA MEGDR ~463 m topography
│   │   ├── thermal/                  # Odyssey THEMIS / MGS TES day/night thermal & thermal inertia
│   │   ├── volatiles/                # Mars Odyssey GRS water-equivalent hydrogen (WEH wt%) & SWIM ice
│   │   └── craters/                  # Robbins & Hynek Mars Crater Database (> 1 km)
│   └── moon/                         # Lunar orbital datasets
│       ├── dem/                      # LRO LOLA GDR ~118 m polar & global elevation
│       ├── thermal/                  # LRO Diviner bolometric brightness temperature (T_max, T_min)
│       ├── mineralogy/               # Clementine UVVIS / Kaguya FeO and TiO2 maps
│       ├── volatiles/                # Lunar Prospector Neutron Spectrometer (LP-NS) epithermal flux
│       └── craters/                  # Head et al. & LRO global crater catalogs
│
├── processed/                        # Processed parameter matrices and cached grids
│   └── earth_analog_catalog.json     # Standard 128-cell terrestrial candidate catalog
│
└── catalogs/                         # Characterized analog catalogs and target site registries
    ├── earth_analog_catalog.json     # 128 Characterized Terrestrial Candidate Cells
    └── target_sites.json             # Curated Moon & Mars exploration landing sites
```

---

## The 128 Earth Analog Candidate Catalog

The benchmark terrestrial catalog (`data/catalogs/earth_analog_catalog.json`) features **128 rigorously characterized equal-area cells** (25.0 km footprint) spanning diverse terrestrial analog environments:
1. **Impact Structures**: Manicouagan, Barringer (Meteor Crater), Vredefort, Nördlinger Ries, Sudbury, Chicxulub, Gosses Bluff, Clearwater.
2. **Volcanic Provinces & Shield Fields**: Mauna Kea / Mauna Loa (Hawaii), Decan Traps, Columbia River Basalts, Iceland Neovolcanic Zone, Mount Etna.
3. **Hyper-Arid Deserts & Regolith**: Atacama Desert (Chile), McMurdo Dry Valleys (Antarctica), Namib Desert, Mojave Desert.
4. **Cryospheric & Polar Permafrost**: Svalbard, Devon Island (Haughton Crater), Greenland Ice Sheet margin, Ellesmere Island.

Each tile stores normalized metrics across all 5 scientific parameter groups:
- **Terrain**: Mean elevation, slope, TRI roughness, local relief, elevation std dev.
- **Mineralogy**: Primary lithology classification, mafic fraction, diagnostic mineral abundance.
- **Thermal**: Maximum diurnal temperature ($T_\text{max}$), diurnal range ($\Delta T$), estimated thermal inertia.
- **Volatiles**: Surface water fraction, glacier/ice area fraction, proxy equivalent hydrogen.
- **Geology**: Impact crater density, age classification, tectonic/volcanic structural setting.

---

## Data Governance & Licensing Notice

Raw raster datasets are downloaded from public scientific archives:
- **NASA PDS Geosciences Node**: LRO LOLA, Diviner, MGS MOLA, Odyssey THEMIS.
- **USGS Astrogeology**: Clementine UVVIS FeO/TiO2, Viking mosaics.
- **Copernicus / NOAA NCEI**: ETOPO 2022 global topography, MODIS Land Products.

*Raw binary rasters exceeding GitHub's 100 MB file limit are maintained locally and excluded via `.gitignore`.*
