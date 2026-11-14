# TerraTwin System Architecture

TerraTwin is an end-to-end multi-parameter planetary exploration and comparative science platform designed to discover, benchmark, and visualize terrestrial analogs for target sites across the Moon and Mars.

---

## 1. High-Level System Architecture

```text
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                       |
|  - Three.js 3D Spherical Celestial Bodies (Earth, Moon, Mars)                           |
|  - Leaflet 2D Cartographic Synchronizer (NASA Trek WMTS)                                |
|  - Dynamic 5-Axis Radar Profile Visualization (Chart.js)                                |
|  - Mission Telemetry HUD & Curated Exploration Landmarks                                |
+--------------------------------------------+--------------------------------------------+
                                             | HTTP / REST API
                                             v
+-----------------------------------------------------------------------------------------+
|                               FASTAPI BACKEND CONTROLLER                                |
|  - GET  /api/health       : Multi-mission dataset & disk storage health                 |
|  - GET  /api/targets      : Curated extraterrestrial target catalog                     |
|  - POST /api/extract      : Multi-mission 5-group coordinate tile extraction            |
|  - POST /api/match        : Normalized Earth analog discovery & ranking engine          |
+--------------------+-----------------------------------------------+--------------------+
                     |                                               |
                     v                                               v
+---------------------------------------+   +---------------------------------------------+
|    TILE EXTRACTION PIPELINE (5-GROUP) |   |        SIMILARITY & BENCHMARKING ENGINE     |
| 1. Terrain Geomorphometry (LOLA/MOLA) |   | - Dynamic Missing-Group Masking             |
| 2. Mineralogy & Lithology (GLiM/TES)  |   | - Normalized Cosine & Euclidean Metrics     |
| 3. Thermophysics (Diviner/THEMIS)     |   | - User-Adjustable Multi-Domain Weights      |
| 4. Volatiles & Ice (LP-NS/SWIM/JRC)   |   | - Scientific Safeguard Threshold (>= 60%)   |
| 5. Geological Context & Impact PASSC  |   | - Rationale Generation & Confidence Bounds  |
+--------------------+------------------+   +----------------------+----------------------+
                     |                                             |
                     +----------------------+----------------------+
                                            |
                                            v
+-----------------------------------------------------------------------------------------+
|                               SCIENTIFIC DATA LAYER                                     |
|  - 128 Characterized Terrestrial Candidate Cells (data/catalogs/earth_analog_catalog.json) |
|  - Planetary DEMs (LRO LOLA GDR, MGS MOLA MEGDR, ETOPO 2022)                           |
|  - Thermal & Lithologic Global Mosaics (MODIS, Diviner, THEMIS, GLiM)                   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Core Scientific Methodologies

### 2.1 Multi-Parameter Extraction Pipeline
When a coordinate is inspected on the Moon, Mars, or Earth:
1. **Equal-Area Footprint**: Computes a local planar bounding window corresponding to an equal-area $25.0 \times 25.0\text{ km}$ footprint.
2. **Terrain Geomorphometry**: Computes elevation, slope (Horn 1981 algorithm), Terrain Ruggedness Index (Riley et al. 1999), and local relief.
3. **Thermophysical Inversion**: Reads diurnal surface temperatures and evaluates calibrated thermal inertia ($J \cdot m^{-2} \cdot K^{-1} \cdot s^{-1/2}$).
4. **Volatiles Assessment**: Queries water-equivalent hydrogen proxies, surface ice/glacier area fractions, and permanent shadow indicators.
5. **Geological Context**: Evaluates impact crater chronometry and lithologic classifications.

### 2.2 Similarity Scoring & Safeguards
$$\text{Composite Similarity} = \frac{\sum_{i \in \text{Observed}} w_i \cdot S_i}{\sum_{i \in \text{Observed}} w_i}$$

- **Dynamic Missing-Data Masking**: Missing or unobserved parameters are represented as `None`/`NaN` and are strictly excluded from calculations (never treated as zero).
- **Minimum Valid Coverage Threshold**: Candidates must possess $\ge 60\%$ mutually observed valid weighted coverage to qualify as a legitimate match.
- **Scientific Transparency**: The system explicitly reports the valid group count (e.g. `3 of 5 groups available`) alongside every composite score.
