# Asterix: Multi-Parameter Planetary Analog Discovery Platform

[![Asterix CI](https://github.com/riyarbhatt1310-tech/NASA_Hackathon_2026_Beyond_Andromeda/actions/workflows/ci.yml/badge.svg)](https://github.com/riyarbhatt1310-tech/NASA_Hackathon_2026_Beyond_Andromeda/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black.svg)](https://threejs.org/)
[![NASA Space Apps](https://img.shields.io/badge/NASA%20Space%20Apps-2026-critical.svg)](https://www.spaceappschallenge.org/)

**Asterix** is an end-to-end planetary exploration and comparative planetology platform that connects extraterrestrial targets on the **Moon** and **Mars** with their highest-fidelity **Earth analogs**. By harmonizing multi-mission orbital remote sensing data across five distinct domains, Asterix enables mission planners, geologists, and planetary scientists to identify terrestrial field sites that mirror the geomorphology, mineralogy, thermophysics, volatile proxies, and geological contexts of landing zones across our solar system.

---

## Table of Contents
- [1. Problem Statement](#1-problem-statement)
- [2. Key Features](#2-key-features)
- [3. System Architecture](#3-system-architecture)
- [4. Technology Stack](#4-technology-stack)
- [5. Repository Structure](#5-repository-structure)
- [6. Installation Instructions](#6-installation-instructions)
- [7. Frontend Startup Instructions](#7-frontend-startup-instructions)
- [8. Backend Startup Instructions](#8-backend-startup-instructions)
- [9. REST API Documentation](#9-rest-api-documentation)
- [10. Scientific Datasets & Data Provenance](#10-scientific-datasets--data-provenance)
- [11. Similarity & Matching Methodology](#11-similarity--matching-methodology)
- [12. Testing & Scientific Validation](#12-testing--scientific-validation)
- [13. Limitations & Future Scope](#13-limitations--future-scope)
- [14. Scientific Governance Notice](#14-scientific-governance-notice)
- [15. Team & Acknowledgments](#15-team--acknowledgments)

---

## 1. Problem Statement

Planetary exploration missions (such as NASA Artemis, Mars Sample Return, and commercial lunar landers) demand extensive terrestrial testing of robotic rovers, autonomous navigation algorithms, drill mechanisms, and instrumentation before flight. Historically, finding terrestrial analog sites has relied on qualitative, single-parameter geological intuition—often focusing solely on visual terrain resemblance while ignoring thermal regimes, mineral chemistry, or volatile proxy metrics.

**TerraTwin solves this by establishing a multi-parameter quantitative similarity engine**:
- Ingests authentic multi-mission orbital rasters across Earth, Moon, and Mars.
- Analyzes normalized equal-area tiles ($25.0 \times 25.0\text{ km}$ footprint).
- Enforces strict scientific safeguards against missing data misrepresentation.
- Provides interactive 3D cartographic inspection and multidimensional radar benchmarking.

---

## 2. Key Features

- **Immersive 3D Planetary Cartography**:
  - Physically illuminated 3D WebGL globes for Earth, Moon, and Mars with calibrated ACES tone mapping.
  - Interactive spherical raycasting allowing surface coordinate inspection and holographic telemetry badges.
  - Curated landmark beacons marking certified safe landing points (e.g., Apollo 11, Shackleton Crater Rim, Jezero Crater).
- **Five-Group Multi-Domain Extraction**:
  1. *Terrain Geomorphometry*: Mean elevation, slope (Horn 1981), Terrain Ruggedness Index (Riley 1999), and local relief.
  2. *Mineralogy & Composition*: FeO/TiO₂ weight percentages, diagnostic mafic fractions, and lithologic unit classifications.
  3. *Thermophysical Environment*: Diurnal temperatures ($T_\text{max}$, $T_\text{min}$, $\Delta T$) and calibrated thermal inertia.
  4. *Water, Ice & Volatiles*: Epithermal neutron hydrogen proxies, surface ice/glacier coverage, and hydrological fractions.
  5. *Geological Context & Landforms*: Impact crater chronometry, structural setting, and crater preservation states.
- **Scientific Similarity Engine**:
  - Weighted multi-parameter cosine and Euclidean similarity ranking.
  - Strict missing-data governance: unobserved groups are masked out and excluded—never coerced to zero.
  - Mandatory $\ge 60\%$ mutually observed valid coverage threshold to qualify matches.
- **Multidimensional Radar Profiling**:
  - Interactive 5-axis polygonal radar charts rendering unobserved domains as distinct scientific gaps.

---

## 3. System Architecture

```text
                                  +-------------------------------------------------------+
                                  |                 USER INTERFACE (SPA)                  |
                                  |  - 3D WebGL Spheres (Three.js + OrbitControls)        |
                                  |  - 2D Cartographic Synchronizer (Leaflet + NASA Trek) |
                                  |  - 5-Axis Radar Profiles (Chart.js)                   |
                                  +---------------------------+---------------------------+
                                                              | HTTP / REST
                                                              v
+-------------------------------------------------------------------------------------------------------------------------+
|                                                   FASTAPI BACKEND                                                       |
|  - GET  /api/health       : System verification, multi-mission sensor integrity & storage capacity                      |
|  - GET  /api/targets      : Curated extraterrestrial target sites catalog                                               |
|  - POST /api/extract      : Multi-parameter tile feature extraction for 25.0 km footprint                              |
|  - POST /api/match        : Multi-domain normalized Earth analog discovery & ranking engine                            |
+------------------------------------+----------------------------------------------------+-------------------------------+
                                     |                                                    |
                                     v                                                    v
+---------------------------------------------------------+      +--------------------------------------------------------+
|          TILE EXTRACTION PIPELINE (5 GROUPS)            |      |            SIMILARITY & BENCHMARKING ENGINE            |
| - LOLA / MOLA Topography Extractors                     |      | - Normalized Cosine & Euclidean Multi-Domain Scoring   |
| - Diviner / THEMIS / MODIS Thermophysics                |      | - User-Adjustable 5-Axis Weighting Matrix              |
| - GLiM Lithology & Mineral Chemistry Ingestion          |      | - Coverage Safeguard Enforcement (Threshold >= 60%)    |
| - Volatiles Proxies (LP-NS, GRS SWIM, HydroSHEDS)       |      | - Automated Rationale Generation                       |
+------------------------------------+--------------------+      +------------------------+-------------------------------+
                                     |                                                    |
                                     +-------------------------+--------------------------+
                                                               |
                                                               v
+-------------------------------------------------------------------------------------------------------------------------+
|                                                  DATA & CATALOG LAYER                                                   |
|  - 128 Characterized Terrestrial Candidate Cells (data/catalogs/earth_analog_catalog.json)                              |
|  - Planetary Rasters: LRO LOLA GDR, MGS MOLA MEGDR, ETOPO 2022 Global DEM                                               |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Technology Stack

- **Backend**:
  - **Framework**: [FastAPI](https://fastapi.tiangolo.com/) with asynchronous ASGI runtime ([Uvicorn](https://www.uvicorn.org/)).
  - **Data Processing**: [NumPy](https://numpy.org/), [Rasterio](https://rasterio.readthedocs.io/), [GDAL](https://gdal.org/), [SciPy](https://scipy.org/).
  - **Validation & Serialization**: [Pydantic v2](https://docs.pydantic.dev/).
  - **Testing**: [Pytest](https://docs.pytest.org/), [HTTPX](https://www.python-httpx.org/).
- **Frontend**:
  - **3D Graphics**: [Three.js r128](https://threejs.org/) with ACES Filmic Tone Mapping.
  - **2D Cartography**: [Leaflet 1.9.4](https://leafletjs.com/) with NASA GIBS / Trek WMTS layers.
  - **Charts & Telemetry**: [Chart.js 4](https://www.chartjs.org/).
  - **Tooling**: Standard ES6 modules + [Vite](https://vitejs.dev/) development server.

---

## 5. Repository Structure

```text
TerraTwin/
├── frontend/                         # Modern frontend application
│   ├── public/
│   │   ├── assets/                   # Vector graphics and UI icons
│   │   └── textures/                 # Planetary textures (Earth, Moon, Mars, Nebula)
│   ├── src/
│   │   ├── components/               # UI components (globe.js, radar)
│   │   ├── services/                 # Centralized API service client (api.js)
│   │   ├── styles/                   # Aerospace UI stylesheet (terratwin.css)
│   │   └── app.js                    # Main frontend state machine & controller
│   ├── index.html                    # Single-page dashboard entry point
│   ├── package.json                  # Node package configuration
│   ├── vite.config.js                # Vite development server configuration
│   └── README.md                     # Frontend documentation
│
├── backend/                          # High-performance FastAPI application
│   ├── app/
│   │   ├── api/                      # API routing modules
│   │   ├── core/                     # Configuration, physical constants & metrics
│   │   ├── processing/               # Tile extraction pipeline & PDS raster readers
│   │   ├── services/                 # Similarity engine & Earth catalog manager
│   │   ├── models/                   # Pydantic request/response schemas
│   │   └── main.py                   # FastAPI server entry point
│   ├── requirements.txt              # Python production dependencies
│   ├── .env.example                  # Environment configuration template
│   └── README.md                     # Backend API documentation
│
├── data/                             # Scientific data repositories
│   ├── raw/                          # Planetary rasters (git-ignored, maintained locally)
│   ├── processed/                    # Processed raster grids
│   ├── catalogs/                     # Characterized 128 Earth analog candidate catalog
│   └── README.md                     # Data catalog documentation & provenance
│
├── scripts/                          # Pipeline utility & maintenance scripts
│   ├── download/                     # Automated data downloaders
│   ├── processing/                   # Batch ingestion & extraction scripts
│   └── validation/                   # Dataset integrity verification scripts
│
├── tests/                            # Comprehensive automated test suite (96 tests)
│   ├── unit/                         # Mathematical & reader unit tests
│   ├── integration/                  # End-to-end API & multi-group pipeline tests
│   └── README.md                     # Testing instructions
│
├── docs/                             # Project documentation & scientific reports
│   ├── architecture/                 # System architecture specifications
│   ├── milestones/                   # Milestone roadmap & development plan
│   ├── data-sources/                 # Comprehensive data sources inventory
│   ├── reports/                      # Scientific validation & engineering reports
│   └── README.md                     # Documentation index
│
├── config/
│   └── config.yaml                   # Global application configuration
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated GitHub Actions CI pipeline
│
├── .gitignore                        # Git exclusion rules
├── README.md                         # Project overview and documentation
├── LICENSE                           # Open-source MIT License
└── CONTRIBUTING.md                   # Contribution guidelines
```

---

## 6. Installation Instructions

### Prerequisites
- **Python**: Version 3.11, 3.12, or 3.13.
- **Node.js** *(Optional, only for Vite dev server)*: Version 18.0+.
- **Git**.

### Clone the Repository
```powershell
git clone https://github.com/riyarbhatt1310-tech/NASA_Hackathon_2026_Beyond_Andromeda.git
cd NASA_Hackathon_2026_Beyond_Andromeda
```

### Python Virtual Environment Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate virtual environment (Linux / macOS)
# source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install pytest pytest-cov httpx
```

---

## 7. Frontend Startup Instructions

TerraTwin supports two flexible ways to run the frontend:

### Option A: Direct FastAPI Serving (Recommended & Fastest)
The FastAPI backend serves the complete single-page application out of the box at `http://localhost:8000`:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Option B: Standalone Vite Development Server
If you are developing frontend components with live module reloading:
```powershell
cd frontend
npm install
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)**. Vite automatically proxies API requests to `http://127.0.0.1:8000`.

---

## 8. Backend Startup Instructions

Start the FastAPI application with live code reloading:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Documentation (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 9. REST API Documentation

### `GET /api/health`
Verifies backend operational status, active planetary bodies, available parameter groups, and free disk space.
```json
{
  "status": "healthy",
  "service": "TerraTwin Multi-Parameter Planetary Analog Discovery API",
  "version": "1.0.0",
  "planetary_bodies": ["moon", "mars", "earth"],
  "earth_catalog_tiles": 128
}
```

### `GET /api/targets`
Retrieves curated exploration targets and safe landing sites on the Moon and Mars.
- **Query Parameter**: `body` (`moon` or `mars`, optional).

### `POST /api/extract`
Extracts all 5 scientific parameter groups for any coordinate on Moon, Mars, or Earth.
```json
// POST /api/extract
{
  "body": "moon",
  "lat": 0.674,
  "lon": 23.473
}
```

### `POST /api/match`
Evaluates and ranks the top-K Earth analogs against the 128 candidate cells using user-defined weights.
```json
// POST /api/match
{
  "body": "moon",
  "lat": 0.674,
  "lon": 23.473,
  "weights": {
    "terrain": 25,
    "mineral": 20,
    "thermal": 20,
    "water": 15,
    "geology": 20
  },
  "top_k": 5,
  "min_coverage": 0.60,
  "include_unqualified": true
}
```

---

## 10. Scientific Datasets & Data Provenance

| Body | Remote Sensing Instrument / Dataset | Agency / Source | Physical Parameter Group | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **Moon** | Lunar Reconnaissance Orbiter (LOLA GDR) | NASA PDS | 1. Terrain Geomorphometry | ~118 m/pixel |
| **Moon** | Clementine UVVIS FeO & TiO₂ | USGS Astrogeology | 2. Mineralogy & Composition | 100 m/pixel |
| **Moon** | LRO Diviner Lunar Radiometer Experiment | NASA PDS / UCLA | 3. Thermophysics ($T_\text{max}$, $T_\text{min}$) | 128 ppd |
| **Moon** | Lunar Prospector Neutron Spectrometer (LP-NS) | NASA PDS | 4. Water, Ice & Volatiles | ~43 km footprint |
| **Moon** | Head et al. Global Lunar Crater Database | Brown University | 5. Geological Context | Diameter $\ge 20\text{ km}$ |
| **Mars** | Mars Global Surveyor (MOLA MEGDR) | NASA PDS | 1. Terrain Geomorphometry | ~463 m/pixel |
| **Mars** | MGS Thermal Emission Spectrometer (TES) | ASU / NASA PDS | 2. Mineralogy & Lithology | ~3 km/pixel |
| **Mars** | 2001 Mars Odyssey (THEMIS IR) | ASU / NASA PDS | 3. Thermophysics & Thermal Inertia | 100 m/pixel |
| **Mars** | Mars Odyssey GRS Water-Equivalent Hydrogen | NASA PDS | 4. Water, Ice & Volatiles | ~600 km footprint |
| **Mars** | Robbins & Hynek Mars Crater Database | NASA PDS | 5. Geological Context | Diameter $\ge 1\text{ km}$ |
| **Earth** | Copernicus DEM / NOAA NCEI ETOPO 2022 | NOAA / Copernicus | 1. Terrain Geomorphometry | 60 arc-seconds |
| **Earth** | GLiM Global Lithological Map | University of Hamburg | 2. Mineralogy & Lithology | 0.5° grid |
| **Earth** | Terra/Aqua MODIS (MOD11C3 L3 LST) | NASA LP DAAC | 3. Thermophysics & Thermal Inertia | 0.05° (~5.6 km) |
| **Earth** | HydroSHEDS / JRC Global Surface Water | European Commission / WWF | 4. Water, Ice & Volatiles | 30 arc-seconds |
| **Earth** | Earth Impact Database (PASSC) | University of New Brunswick | 5. Geological Context | Confirmed structures |

---

## 11. Similarity & Matching Methodology

1. **Equal-Area Normalization**: Target and candidate coordinates are evaluated across an equal-area $25.0 \times 25.0\text{ km}$ footprint.
2. **Domain Similarity Scoring**:
   - Terrain similarity evaluates cosine distance across normalized vectors: $\langle \text{elevation}, \text{slope}, \text{TRI}, \text{relief} \rangle$.
   - Thermal similarity benchmarks diurnal temperature extrema ($T_\text{max}$, $\Delta T$) and thermal inertia.
   - Volatiles similarity compares water-equivalent hydrogen proxy metrics and cryospheric glacier fractions.
3. **Composite Similarity**:
   $$\text{Composite Score} = \frac{\sum_{i \in \text{Observed}} w_i \cdot S_i}{\sum_{i \in \text{Observed}} w_i}$$
4. **Coverage Safeguard Enforcement**:
   - Missing remote-sensing domains remain `None`/`NaN` and are strictly excluded from calculation.
   - If mutually observed weighted coverage falls below the configured threshold (default $60\%$), the match is flagged as **Unqualified** (`is_qualified_match: false`).

---

## 12. Testing & Scientific Validation

TerraTwin includes 96 comprehensive automated tests covering unit math, PDS raster readers, and integration pipelines:

```powershell
# Run the complete test suite
pytest

# Run tests with execution timings
pytest -v --durations=10
```

### Verified Scientific Scenarios
- **Scenario 1**: Moon — Apollo 11 Landing Site (`0.674° N, 23.473° E`).
  - Correctly matches high-titanium terrestrial impact structures (Manicouagan, Meteor Crater).
- **Scenario 2**: Moon — Shackleton Crater (`-89.5° S, 0.0° E`).
  - Permanently shadowed cryogenic conditions benchmarked against polar cryospheric analogs (Haughton Crater, Svalbard).
- **Scenario 3**: Mars — Jezero Crater (`18.38° N, 77.58° E`).
  - Lacustrine sedimentary delta and basaltic margin matched to terrestrial paleolake basins.

---

## 13. Limitations & Future Scope

- **Global Raster Footprints**: High-resolution planetary datasets currently span representative target regions; planetary-wide seamless rasters require external tile streaming.
- **Instrument Footprint Discrepancies**: Epithermal neutron footprints (~43 km for LP-NS, ~600 km for Mars GRS) operate at coarser spatial scales than laser altimetry (~118 m for LOLA).
- **Future Enhancements**:
  - Integration of high-resolution HiRISE and LRO NAC sub-meter imaging tiles.
  - Machine-learning driven terrain feature classification for micro-scale rover hazard mapping.

---

## 14. Scientific Governance Notice

> **IMPORTANT SCIENTIFIC NOTICE**:  
> Relative similarity scores represent comparative physical geomorphometry, mineralogy, thermophysics, and volatile proxy correspondence derived from multi-mission orbital remote-sensing datasets. They do **NOT** indicate biological potential, exact environmental equivalence, or human habitability.

---

## 15. Team & Acknowledgments

Developed for the **NASA International Space Apps Challenge 2026**.

- **Repository**: [https://github.com/riyarbhatt1310-tech/NASA_Hackathon_2026_Beyond_Andromeda](https://github.com/riyarbhatt1310-tech/NASA_Hackathon_2026_Beyond_Andromeda)
- **Acknowledgments**: NASA Planetary Data System (PDS), USGS Astrogeology Science Center, NOAA National Centers for Environmental Information, European Commission Joint Research Centre (JRC), and the global planetary science community.
