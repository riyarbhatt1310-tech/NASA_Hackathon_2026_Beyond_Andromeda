"""
Configuration loader and validator for TerraTwin.
Supports config.yaml, environment variable overrides, and path resolution.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Determine project root (terratwin directory)
# Dynamically resolves whether running from backend/app/core or src/core
_resolved = Path(__file__).resolve()
if (_resolved.parent.parent.parent.parent / "config" / "config.yaml").is_file():
    PROJECT_ROOT = _resolved.parent.parent.parent.parent
elif (_resolved.parent.parent.parent / "config" / "config.yaml").is_file():
    PROJECT_ROOT = _resolved.parent.parent.parent
else:
    PROJECT_ROOT = _resolved.parent.parent.parent.parent


def get_default_config_path() -> Path:
    """Returns the default path to config.yaml."""
    return PROJECT_ROOT / "config" / "config.yaml"


class Config:
    """Configuration manager for TerraTwin."""

    def __init__(self, config_dict: Dict[str, Any], config_path: Optional[Path] = None):
        self.raw = config_dict
        self.config_path = config_path or get_default_config_path()
        self.project = config_dict.get("project", {})
        self.moon = config_dict.get("moon", {})
        self.mars = config_dict.get("mars", {})
        self.earth = config_dict.get("earth", {})
        self.analysis = config_dict.get("analysis", {})

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Loads configuration from a YAML file."""
        path = Path(config_path) if config_path else get_default_config_path()
        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Allow environment variable overrides for file paths
        if "TERRATWIN_MOON_RASTER" in os.environ:
            data.setdefault("moon", {})["raster_path"] = os.environ["TERRATWIN_MOON_RASTER"]
        if "TERRATWIN_MOON_LABEL" in os.environ:
            data.setdefault("moon", {})["label_path"] = os.environ["TERRATWIN_MOON_LABEL"]
        if "TERRATWIN_MARS_RASTER" in os.environ:
            data.setdefault("mars", {})["raster_path"] = os.environ["TERRATWIN_MARS_RASTER"]
        if "TERRATWIN_MARS_METADATA" in os.environ:
            data.setdefault("mars", {})["metadata_path"] = os.environ["TERRATWIN_MARS_METADATA"]
        if "TERRATWIN_EARTH_DEM" in os.environ:
            data.setdefault("earth", {})["dem_path"] = os.environ["TERRATWIN_EARTH_DEM"]

        return cls(data, path)

    def resolve_path(self, relative_or_absolute: str) -> Path:
        """Resolves a path relative to the project root if not absolute."""
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p
        return (PROJECT_ROOT / p).resolve()

    def get_moon_raster_path(self) -> Path:
        """Returns the resolved path to Moon LOLA raster."""
        rel = self.moon.get("raster_path", "data/raw/moon/LDEM_16_FLOAT.IMG")
        return self.resolve_path(rel)

    def get_moon_label_path(self) -> Path:
        """Returns the resolved path to Moon LOLA label."""
        rel = self.moon.get("label_path", "data/raw/moon/LDEM_16_FLOAT.LBL")
        return self.resolve_path(rel)

    def get_mars_raster_path(self) -> Path:
        """Returns the resolved path to Mars MOLA raster."""
        rel = self.mars.get("raster_path", "data/raw/mars/megt90n000eb.img")
        return self.resolve_path(rel)

    def get_mars_metadata_path(self) -> Path:
        """Returns the resolved path to Mars MOLA metadata."""
        rel = self.mars.get("metadata_path", "data/raw/mars/megt90n000eb.xml")
        return self.resolve_path(rel)

    def get_earth_dem_path(self) -> Path:
        """Returns the resolved path to Earth DEM raster."""
        rel = self.earth.get("dem_path", "data/raw/earth/dem/ETOPO_2022_v1_60s_N90W180_surface.tif")
        return self.resolve_path(rel)

    def validate_file_existence(self) -> Dict[str, bool]:
        """Checks whether configured planetary DEM files exist on disk."""
        return {
            "moon_raster": self.get_moon_raster_path().is_file(),
            "moon_label": self.get_moon_label_path().is_file(),
            "mars_raster": self.get_mars_raster_path().is_file(),
            "mars_metadata": self.get_mars_metadata_path().is_file(),
            "earth_dem": self.get_earth_dem_path().is_file(),
        }
