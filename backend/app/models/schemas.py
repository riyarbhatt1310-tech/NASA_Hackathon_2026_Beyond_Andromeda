"""
Pydantic Schemas and Request/Response Models for TerraTwin API.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    """Request payload for multi-parameter tile extraction."""
    body: str = Field(..., description="'moon', 'mars', or 'earth'")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., description="Longitude in decimal degrees (will be normalized to [-180, 180])")


class MatchRequest(BaseModel):
    """Request payload for global Earth analog matching and ranking."""
    body: str = Field(..., description="Target planetary body: 'moon' or 'mars'")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Target latitude in decimal degrees")
    lon: float = Field(..., description="Target longitude in decimal degrees")
    weights: Optional[Dict[str, float]] = Field(None, description="Custom 5-axis weights: terrain, mineral, thermal, water, geology")
    top_k: int = Field(5, ge=1, le=50, description="Number of ranked Earth analogs to return")
    min_coverage: float = Field(0.60, ge=0.0, le=1.0, description="Minimum valid weighted coverage threshold (default 60%)")
    include_unqualified: bool = Field(True, description="Whether to include candidates falling below min_coverage (marked qualified=False)")
