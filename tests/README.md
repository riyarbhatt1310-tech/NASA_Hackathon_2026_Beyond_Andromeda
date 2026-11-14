# TerraTwin Automated Test Suite

TerraTwin includes a comprehensive, scientifically rigorous test suite verifying physical geomorphometry calculations, PDS raster ingestion, thermal inertia calibration, 5-group tile extraction, similarity scoring, and FastAPI REST endpoints.

---

## Test Directory Architecture

```text
tests/
├── unit/                               # Mathematical & reader unit tests
│   ├── test_metrics.py                 # Slope (Horn 1981), TRI (Riley 1999), relief & hypsometry
│   ├── test_ti_calibration.py          # Empirical thermal inertia calibration equations
│   ├── test_readers.py                 # PDS3 LBL/IMG binary readers & nodata handling
│   ├── test_thermal_readers.py         # Diviner & THEMIS day/night thermal raster units
│   ├── test_volatiles_geology_synthetic.py  # Volatiles proxy & crater chronometry calculations
│   └── test_similarity_engine.py      # Cosine similarity, weight normalization & coverage safeguards
│
├── integration/                        # End-to-end integration & API tests
│   ├── test_api.py                     # FastAPI REST API contract (/api/health, /api/extract, etc.)
│   ├── test_tile_extractor_5group.py   # Multi-mission 5-group feature aggregation pipeline
│   ├── test_tile_extractor_thermal.py  # Thermal & thermal inertia feature extractor integration
│   ├── test_real_thermal_extraction.py # Real raster thermal extraction validation
│   ├── test_real_volatiles_geology.py  # Real volatiles and geological catalog ingestion
│   ├── test_earth_dem.py               # Global Earth DEM (Copernicus/ETOPO) ingestion pipeline
│   ├── test_ui_phase1.py               # Landing page, telemetry contract & coordinate selection
│   └── test_ui_phase2.py               # Calibrated 3D visual visibility & research console contract
│
└── README.md
```

---

## Running Tests

From the project root:

```powershell
# Run the complete test suite
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with verbose output and coverage
pytest -v --durations=10
```

### Coverage & Safeguards
- **Coverage Enforcement**: Tests verify that composite similarity calculations never treat unobserved or missing parameters as zero.
- **Scientific Safeguard**: Results with < 60% valid weighted coverage are strictly flagged as unqualified.
- **Physical Boundary Verification**: Confirms slopes $\in [0, 90]^\circ$, TRI $\ge 0$, and thermal temperatures conform to physical sensor bounds.
