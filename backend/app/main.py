"""TerraTwin FastAPI Backend Application.

Provides RESTful endpoints for:
- Health check and system verification (/api/health)
- Curated extraterrestrial target sites on Moon and Mars (/api/targets)
- Multi-parameter tile feature extraction across all 5 groups (/api/extract)
- Global Earth analog discovery & ranking engine (/api/match)
- Serving the interactive single-page dashboard UI (/)
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.core.config import Config
from src.core.constants import ANALYSIS_TILE_SIZE_KM
from src.processing.tile_extractor import PlanetaryTileExtractor
from src.processing.similarity_engine import MultiParameterSimilarityEngine, DEFAULT_WEIGHTS
from src.processing.earth_catalog import EarthCatalogManager
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader
from src.data_ingestion.moon_diviner import MoonDivinerReader
from src.data_ingestion.mars_thermis import MarsThermisReader
from src.data_ingestion.mars_tes_temp import MarsTesTempReader
from src.data_ingestion.earth_modis import ModisLSTReader
from src.data_ingestion.earth_glim import EarthGLiMAggregator
from src.data_ingestion.earth_water import EarthWaterAggregator
from src.data_ingestion.moon_volatiles import MoonVolatilesReader
from src.data_ingestion.mars_volatiles import MarsVolatilesReader
from src.data_ingestion.crater_catalog import PlanetaryCraterCatalog
from src.data_ingestion.earth_impacts import EarthImpactCatalog
from src.data_ingestion.geologic_units import GeologicUnitAggregator

# Initialize FastAPI App
app = FastAPI(
    title="Asterix: Multi-Parameter Planetary Analog Discovery Platform",
    description="Scientific 5-group planetary feature extraction and comparative similarity engine across Earth, Moon, and Mars.",
    version="1.0.0",
)

# Enable CORS for external frontend or notebooks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mandatory Scientific Disclaimer
SCIENTIFIC_DISCLAIMER = (
    "Scientific Governance Notice: Relative similarity scores represent comparative physical "
    "geomorphometry, mineralogy, thermophysics, and volatile proxy correspondence derived from "
    "multi-mission orbital remote-sensing datasets. They do NOT indicate biological potential, "
    "exact environmental equivalence, or human habitability."
)

# Base Paths
_p = Path(__file__).resolve()
if len(_p.parents) > 2 and (_p.parents[2] / "data").exists():
    BASE_DIR = _p.parents[2]
else:
    BASE_DIR = _p.parent.parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_PUBLIC = FRONTEND_DIR / "public"
FRONTEND_SRC = FRONTEND_DIR / "src"

# Lazy-loaded singletons
_extractor: Optional[PlanetaryTileExtractor] = None
_earth_catalog: Optional[EarthCatalogManager] = None


def get_extractor() -> PlanetaryTileExtractor:
    """Builds and caches the operational PlanetaryTileExtractor instance."""
    global _extractor
    if _extractor is not None:
        return _extractor

    diviner_day = RAW_DIR / "moon" / "thermal" / "diviner_day.tif"
    diviner_night = RAW_DIR / "moon" / "thermal" / "diviner_night.tif"
    moon_diviner = MoonDivinerReader(str(diviner_day), str(diviner_night)) if diviner_day.exists() else None

    themis_tif = RAW_DIR / "mars" / "thermal" / "themis_ti_jezero_100m.tif"
    mars_themis = MarsThermisReader(str(themis_tif)) if themis_tif.exists() else None

    tes_day = RAW_DIR / "mars" / "thermal" / "global_ti_day_2007.lbl"
    tes_night = RAW_DIR / "mars" / "thermal" / "global_ti_night_2007.lbl"
    mars_tes = MarsTesTempReader(str(tes_day), str(tes_night)) if tes_day.exists() else None

    modis_day = RAW_DIR / "earth" / "thermal" / "modis_lst_day.tif"
    modis_night = RAW_DIR / "earth" / "thermal" / "modis_lst_night.tif"
    modis_qc_day = RAW_DIR / "earth" / "thermal" / "modis_qc_day.tif"
    modis_qc_night = RAW_DIR / "earth" / "thermal" / "modis_qc_night.tif"
    earth_modis = ModisLSTReader(
        str(modis_day), str(modis_night), str(modis_qc_day), str(modis_qc_night)
    ) if modis_day.exists() else None

    glim_path = RAW_DIR / "earth" / "mineralogy" / "glim_global.tif"
    earth_glim = EarthGLiMAggregator(str(glim_path)) if glim_path.exists() else None

    _extractor = PlanetaryTileExtractor(
        moon_reader=MoonLolaReader(),
        mars_reader=MarsMolaReader(),
        moon_diviner_reader=moon_diviner,
        mars_thermis_reader=mars_themis,
        mars_tes_reader=mars_tes,
        earth_glim_aggregator=earth_glim,
        earth_modis_reader=earth_modis,
        earth_water_aggregator=EarthWaterAggregator(),
        moon_volatiles_reader=MoonVolatilesReader(),
        mars_volatiles_reader=MarsVolatilesReader(),
        moon_crater_catalog=PlanetaryCraterCatalog("moon"),
        mars_crater_catalog=PlanetaryCraterCatalog("mars"),
        earth_impact_catalog=EarthImpactCatalog(),
        moon_geology_aggregator=GeologicUnitAggregator("moon"),
        mars_geology_aggregator=GeologicUnitAggregator("mars"),
        earth_geology_aggregator=GeologicUnitAggregator("earth"),
    )
    return _extractor


def get_earth_catalog() -> EarthCatalogManager:
    global _earth_catalog
    if _earth_catalog is None:
        _earth_catalog = EarthCatalogManager()
    return _earth_catalog


# -----------------------------------------------------------------------------
# Curated Targets Catalog
# -----------------------------------------------------------------------------
CURATED_TARGET_SITES = [
    # Moon
    {
        "id": "moon_apollo11",
        "name": "Apollo 11 Landing Site (Mare Tranquillitatis)",
        "body": "moon",
        "lat": 0.674,
        "lon": 23.473,
        "geology": "Imbrian high-titanium basalt plain with low local slope.",
        "primary_feature": "High-Ti flood basalt, lunar regolith maturation, low slope.",
    },
    {
        "id": "moon_shackleton",
        "name": "Shackleton Crater / South Pole",
        "body": "moon",
        "lat": -89.90,
        "lon": 0.00,
        "geology": "Pre-Nectarian polar crater with permanently shadowed cryogenic interior.",
        "primary_feature": "Cryogenic micro-cold trap (< 110 K), steep crater rims.",
    },
    {
        "id": "moon_oceanus_procellarum",
        "name": "Oceanus Procellarum Mare Basalt",
        "body": "moon",
        "lat": 20.00,
        "lon": 300.00,
        "geology": "Extensive Eratosthenian/Imbrian mare flood basalts within the PKT.",
        "primary_feature": "Smooth low-relief plain, elevated Thorium/KREEP geochemical background.",
    },
    {
        "id": "moon_copernicus",
        "name": "Copernicus Impact Crater",
        "body": "moon",
        "lat": 9.62,
        "lon": 339.92,
        "geology": "Prominent Copernican complex impact crater with central peaks and impact melt.",
        "primary_feature": "High local relief (> 3500 m), terraced walls, central peak uplift.",
    },
    # Mars
    {
        "id": "mars_jezero",
        "name": "Jezero Crater (Perseverance Site)",
        "body": "mars",
        "lat": 18.38,
        "lon": 77.58,
        "geology": "Noachian/Hesperian paleolake delta system with phyllosilicates and carbonates.",
        "primary_feature": "Ancient lacustrine delta, clay-carbonate mineralogy, diverse thermal inertia.",
    },
    {
        "id": "mars_olympus_mons",
        "name": "Olympus Mons Caldera",
        "body": "mars",
        "lat": 18.65,
        "lon": 226.20,
        "geology": "Enormous Amazonian basaltic shield volcano caldera complex.",
        "primary_feature": "Massive elevation (> 21 km), extreme relief, low dust cover.",
    },
    {
        "id": "mars_gale",
        "name": "Gale Crater / Mount Sharp (Curiosity Site)",
        "body": "mars",
        "lat": -5.37,
        "lon": 137.44,
        "geology": "Layered sedimentary mound (Aeolis Mons) spanning clay-to-sulfate transition.",
        "primary_feature": "Hydrated sulfate layers, inverted stream channels, stratified sediments.",
    },
    {
        "id": "mars_hellas",
        "name": "Hellas Impact Basin Floor",
        "body": "mars",
        "lat": -42.40,
        "lon": 70.50,
        "geology": "Deepest impact basin on Mars with dense atmosphere and dust mantles.",
        "primary_feature": "Low elevation (-7 km), high atmospheric pressure, aeolian dust cover.",
    },
    {
        "id": "mars_arcadia",
        "name": "Arcadia Planitia Subsurface Ice",
        "body": "mars",
        "lat": 39.30,
        "lon": 189.70,
        "geology": "Amazonian smooth plains underlain by shallow, extensive ground ice sheets.",
        "primary_feature": "High subsurface WEH (> 10 wt%), positive SWIM ice consistency score.",
    },
]


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class ExtractRequest(BaseModel):
    body: str = Field(..., description="'moon', 'mars', or 'earth'")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees")


class MatchRequest(BaseModel):
    body: str = Field(..., description="Target planetary body: 'moon' or 'mars'")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Target latitude in decimal degrees")
    lon: float = Field(..., description="Target longitude in decimal degrees")
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="User-tunable weights for: terrain, mineral, thermal, water, geology. Must be >= 0."
    )
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top ranked Earth analogs to return")
    min_coverage: float = Field(
        default=0.60,
        ge=0.20,
        le=1.0,
        description="Minimum composite valid coverage ratio (min 0.20 to prevent bypassing safeguards)"
    )
    include_unqualified: bool = Field(
        default=True,
        description="Whether to include candidates with insufficient coverage flagged as unqualified"
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Returns service health, available datasets, and system capacity."""
    total, used, free = shutil.disk_usage(BASE_DIR)
    free_gb = round(free / (1024 ** 3), 2)
    cat_len = get_earth_catalog().get_tile_count()

    return {
        "status": "healthy",
        "service": "Asterix Multi-Parameter Planetary Analog Discovery API",
        "version": "1.0.0",
        "planetary_bodies": ["moon", "mars", "earth"],
        "parameter_groups": [
            "1. Terrain Geomorphometry (Horn slope, TRI roughness, relief)",
            "2. Mineralogy & Composition (FeO, TiO2, TES minerals, GLiM lithology)",
            "3. Thermophysical Environment (Day/Night LST, Thermal Inertia)",
            "4. Water, Ice & Volatiles (WEH wt%, JRC water, Glaciers, SWIM)",
            "5. Geological Context & Landforms (Crater chronometry, PASSC impacts)",
        ],
        "earth_catalog_tiles": cat_len,
        "disk_free_gb": free_gb,
        "disclaimer": SCIENTIFIC_DISCLAIMER,
    }


@app.get("/api/targets")
def get_curated_targets(body: Optional[str] = Query(None, description="'moon' or 'mars'")) -> Dict[str, Any]:
    """Returns curated scientifically significant extraterrestrial target sites."""
    if body:
        b_clean = body.lower().strip()
        filtered = [t for t in CURATED_TARGET_SITES if t["body"] == b_clean]
    else:
        filtered = CURATED_TARGET_SITES

    return {
        "count": len(filtered),
        "targets": filtered,
        "disclaimer": SCIENTIFIC_DISCLAIMER,
    }


@app.post("/api/extract")
def extract_tile(req: ExtractRequest) -> Dict[str, Any]:
    """Extracts unified 5-group planetary tile record at given coordinates."""
    b_clean = req.body.lower().strip()
    extractor = get_extractor()

    try:
        if b_clean == "moon":
            record = extractor.extract_moon_tile(req.lat, req.lon)
        elif b_clean == "mars":
            record = extractor.extract_mars_tile(req.lat, req.lon)
        elif b_clean == "earth":
            record = extractor.extract_earth_tile(req.lat, req.lon)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported planetary body '{req.body}'. Choose 'moon', 'mars', or 'earth'."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature extraction error: {str(e)}")

    return {
        "tile": record,
        "disclaimer": SCIENTIFIC_DISCLAIMER,
    }


@app.post("/api/match")
def match_analogs(req: MatchRequest) -> Dict[str, Any]:
    """Finds and ranks top-K Earth analog candidate tiles for target extraterrestrial tile."""
    b_clean = req.body.lower().strip()
    if b_clean not in ("moon", "mars"):
        raise HTTPException(status_code=400, detail="Target body must be 'moon' or 'mars'.")

    # 1. Extract Target Tile Features
    extractor = get_extractor()
    if b_clean == "moon":
        target_tile = extractor.extract_moon_tile(req.lat, req.lon)
    else:
        target_tile = extractor.extract_mars_tile(req.lat, req.lon)

    # 2. Get Earth Candidates
    catalog_mgr = get_earth_catalog()
    candidate_tiles = catalog_mgr.get_all_tiles()

    if not candidate_tiles:
        raise HTTPException(status_code=500, detail="Earth analog catalog is unpopulated.")

    # 3. Calculate Normalized Effective Weights
    raw_weights = req.weights or DEFAULT_WEIGHTS.copy()
    total_w = sum(raw_weights.values())
    if total_w > 0:
        norm_weights_pct = {k: round((v / total_w) * 100.0, 2) for k, v in raw_weights.items()}
    else:
        norm_weights_pct = {k: 20.0 for k in raw_weights}

    # Enforce minimum valid coverage safeguard (cannot bypass via 0%)
    safe_min_coverage = max(0.20, float(req.min_coverage))

    engine = MultiParameterSimilarityEngine(
        weights=raw_weights,
        min_composite_coverage=safe_min_coverage,
    )

    # 4. Rank Candidates
    raw_ranked = engine.rank_candidates(
        target_tile=target_tile,
        candidate_tiles=candidate_tiles,
        top_k=req.top_k,
        include_unqualified=req.include_unqualified,
    )

    # 5. Format Output with Explanations & Effective Resolution
    ranked_analogs = []
    for rank_idx, item in enumerate(raw_ranked, start=1):
        cand = item["candidate_tile"]
        sim = item["similarity"]

        # Missing data warnings
        warnings = []
        for grp, is_valid in sim["parameter_coverage"].items():
            if not is_valid:
                warnings.append(f"Parameter group '{grp}' has insufficient valid coverage (< 70%) in one or both tiles.")

        ranked_analogs.append({
            "rank": rank_idx,
            "name": cand.get("tile_id", f"Earth Tile {rank_idx}"),
            "lat": cand.get("lat_center"),
            "lon": cand.get("lon_center"),
            "analog_category": cand.get("analog_category", "general_terrain"),
            "composite_similarity_pct": sim["composite_similarity_pct"],
            "is_qualified_match": sim["is_qualified_match"],
            "coverage_status": sim["coverage_status"],
            "status_message": sim["status_message"],
            "valid_groups_summary": sim["valid_groups_summary"],
            "valid_group_count": sim["valid_group_count"],
            "total_group_count": sim["total_group_count"],
            "composite_coverage_pct": sim["composite_coverage_pct"],
            "min_coverage_threshold_pct": sim["min_coverage_threshold_pct"],
            "observed_groups": sim["observed_groups"],
            "unobserved_groups": sim["unobserved_groups"],
            "parameter_scores": sim["parameter_scores"],
            "parameter_coverage": sim["parameter_coverage"],
            "composite_coverage_ratio": sim["composite_coverage_ratio"],
            "radar_profile": sim["radar_profile"],
            "scientific_rationale": sim["scientific_rationale"],
            "effective_resolutions_km": {
                "target_terrain": target_tile.get("effective_res_km"),
                "target_volatiles": target_tile.get("volatile_weh_effective_resolution_km"),
                "candidate_volatiles": cand.get("volatile_weh_effective_resolution_km", 0.03),
            },
            "missing_data_warnings": warnings,
        })

    return {
        "target": {
            "body": target_tile.get("body"),
            "lat": target_tile.get("lat_center"),
            "lon": target_tile.get("lon_center"),
            "tile_id": target_tile.get("tile_id"),
            "terrain_valid": target_tile.get("terrain_valid"),
            "mineral_valid": target_tile.get("mineral_valid"),
            "thermal_valid": target_tile.get("thermal_valid"),
            "volatile_valid": target_tile.get("volatile_valid"),
            "geology_valid": target_tile.get("geology_valid"),
            "stratigraphic_unit": target_tile.get("geology_stratigraphic_unit"),
        },
        "query_parameters": {
            "raw_weights": raw_weights,
            "effective_weights_pct": norm_weights_pct,
            "min_coverage_threshold": safe_min_coverage,
            "total_candidates_evaluated": len(candidate_tiles),
            "matches_returned": len(ranked_analogs),
        },
        "ranked_analogs": ranked_analogs,
        "disclaimer": SCIENTIFIC_DISCLAIMER,
    }


# -----------------------------------------------------------------------------
# Static HTML Single-Page Application Dashboard & Modern Frontend Mounts
# -----------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    if (FRONTEND_SRC / "styles").exists():
        app.mount("/static/css", StaticFiles(directory=str(FRONTEND_SRC / "styles")), name="static-css")
    if (FRONTEND_SRC / "components").exists():
        app.mount("/static/js/components", StaticFiles(directory=str(FRONTEND_SRC / "components")), name="static-components")
    if FRONTEND_SRC.exists():
        app.mount("/static/js", StaticFiles(directory=str(FRONTEND_SRC)), name="static-js")
    if (FRONTEND_PUBLIC / "textures").exists():
        app.mount("/static/textures", StaticFiles(directory=str(FRONTEND_PUBLIC / "textures")), name="static-textures")
    if FRONTEND_PUBLIC.exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_PUBLIC)), name="static-public")
else:
    STATIC_DIR = BASE_DIR / "src" / "api" / "static"
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the interactive Asterix planetary analog dashboard."""
    for html_candidate in [FRONTEND_DIR / "index.html", BASE_DIR / "src" / "api" / "static" / "index.html"]:
        if html_candidate.exists():
            with open(html_candidate, "r", encoding="utf-8") as f:
                return f.read()
    return HTMLResponse("<h2>Asterix API Server Running. Dashboard HTML not found.</h2>")
