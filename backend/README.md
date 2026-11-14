# TerraTwin Backend API & Scientific Engine

High-performance [FastAPI](https://fastapi.tiangolo.com/) application and planetary remote-sensing extraction engine powering **TerraTwin**.

---

## Directory Architecture

```text
backend/
├── app/
│   ├── api/                  # API routers and endpoints
│   ├── core/                 # Configuration loader, physical constants, grids & metrics
│   │   ├── config.py         # Config.yaml and environment variable manager
│   │   ├── constants.py      # Volumetric planetary radii and coordinate constants
│   │   ├── grids.py          # Equal-area 25.0 km planetary tile coordinate frames
│   │   └── metrics.py        # Geomorphometric calculations (Horn slope, TRI, relief)
│   ├── processing/           # Multi-mission raster processing & readers
│   │   ├── tile_extractor.py # 5-group scientific tile extraction pipeline
│   │   ├── earth_dem.py      # Global Earth DEM (Copernicus/ETOPO) reader
│   │   ├── moon_lola.py      # LRO LOLA GDR PDS binary reader
│   │   ├── mars_mola.py      # MGS MOLA MEGDR PDS binary reader
│   │   ├── moon_diviner.py   # LRO Diviner bolometric brightness temperature reader
│   │   ├── mars_thermis.py   # Mars Odyssey THEMIS day/night IR reader
│   │   ├── mars_tes_temp.py  # Mars Global Surveyor TES thermal reader
│   │   ├── earth_modis.py    # MODIS MOD11C3 day/night thermal aggregator
│   │   ├── earth_glim.py     # GLiM global high-resolution lithology reader
│   │   ├── earth_water.py    # HydroSHEDS / JRC surface water & glacier fraction
│   │   ├── moon_volatiles.py # Lunar Prospector Neutron Spectrometer reader
│   │   ├── mars_volatiles.py # Mars Odyssey GRS water-equivalent hydrogen (WEH) reader
│   │   ├── crater_catalog.py # Lunar & Martian impact crater chronometry catalogs
│   │   ├── earth_impacts.py  # Earth Impact Database (PASSC) reader
│   │   └── geologic_units.py # USGS planetary stratigraphy & geological unit aggregator
│   ├── services/             # Core business & scientific services
│   │   ├── similarity_engine.py # Multi-domain normalized cosine & Euclidean similarity engine
│   │   └── earth_catalog.py  # 128 Characterized Terrestrial Candidate Cell Manager
│   ├── models/               # Pydantic request and response schemas
│   │   └── schemas.py        # ExtractRequest, MatchRequest
│   └── main.py               # FastAPI application entry point & static server
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md
```

---

## REST API Endpoints

### 1. `GET /api/health`
System status, multi-mission dataset verification, and free disk capacity.

### 2. `GET /api/targets`
List of curated scientific landing sites and exploration landmarks for Moon and Mars.
- **Parameters**: `body` (optional, `'moon'` or `'mars'`)

### 3. `POST /api/extract`
Extracts all 5 scientific parameter groups for a specified planetary coordinate tile ($25\text{ km}$ equal-area footprint).
- **Request Body**:
  ```json
  {
    "body": "moon",
    "lat": 0.674,
    "lon": 23.473
  }
  ```

### 4. `POST /api/match`
Evaluates and ranks global Earth analogs against the characterized 128 candidate cells using user-configured domain weights.
- **Request Body**:
  ```json
  {
    "body": "moon",
    "lat": 0.674,
    "lon": 23.473,
    "weights": { "terrain": 25, "mineral": 20, "thermal": 20, "water": 15, "geology": 20 },
    "top_k": 5,
    "min_coverage": 0.60,
    "include_unqualified": true
  }
  ```

---

## Running the Backend

```powershell
# From project root
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
