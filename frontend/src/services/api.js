/**
 * TerraTwin Frontend API Service
 * Centralized interface for FastAPI backend communication.
 */

const API_BASE = window.location.origin;

export const ApiService = {
  /**
   * Check system health and backend service status.
   */
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Retrieve curated landing sites and landmarks for Moon and Mars.
   */
  async getTargets(body = null) {
    const url = body ? `${API_BASE}/api/targets?body=${body}` : `${API_BASE}/api/targets`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch targets: ${res.statusText}`);
    return res.json();
  },

  /**
   * Extract 5 scientific parameter groups for a specified coordinate tile.
   */
  async extractTile(body, lat, lon) {
    const res = await fetch(`${API_BASE}/api/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body, lat, lon }),
    });
    if (!res.ok) throw new Error(`Extraction failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Run Earth analog matching against characterized candidate catalog.
   */
  async matchAnalogs({ body, lat, lon, weights, minCoverage = 0.60, topK = 5, includeUnqualified = true }) {
    const res = await fetch(`${API_BASE}/api/match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        body,
        lat,
        lon,
        weights,
        min_coverage: minCoverage,
        top_k: topK,
        include_unqualified: includeUnqualified,
      }),
    });
    if (!res.ok) throw new Error(`Matching failed: ${res.statusText}`);
    return res.json();
  },
};
