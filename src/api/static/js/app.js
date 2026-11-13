/**
 * TerraTwin Planetary Exploration Application Controller
 * Phase 2: Calibrated Planetary Visibility + Planetary Science Research Console
 * Handles Landing Screen transitions, 3D Globe & NASA 2D Map synchronization,
 * Live Multi-Parameter Extraction (/api/extract), and Global Earth Analog Matching (/api/match).
 */

// Application State
const state = {
  currentBody: 'moon',
  currentLat: 0.67,
  currentLon: 23.47,
  viewMode: '3d', // '3d', '2d', 'split'
  globe: null,
  showcaseGlobes: {},
  map2d: null,
  map2dMarker: null,
  map2dTileLayer: null,
  planetaryGridLayer: null,
  earthMap: null,
  earthMarkers: [],
  radarChart: null,
  targetsList: [],
  extractedTile: null,
  rankedAnalogs: [],
  selectedCandidateIndex: 0,
  weights: { terrain: 25, mineral: 20, thermal: 20, water: 15, geology: 20 },
  minCoverage: 0.60
};

// Scientific Planetary Telemetry Database
const PLANET_TELEMETRY = {
  moon: {
    name: 'Moon (Luna)',
    role: 'Lunar Cold Traps & Mare Basalts',
    radius: '1,737.4 km',
    gravity: '1.62 m/s² (0.166 g)',
    atmosphere: 'Surface Exosphere (< 10⁻¹² bar)',
    tempRange: '40 K to 395 K (-233°C to +122°C)',
    missions: 'LRO (LOLA, Diviner), Lunar Prospector (LP-NS)'
  },
  mars: {
    name: 'Mars (Ares)',
    role: 'Paleolakes & Volcanic Provinces',
    radius: '3,389.5 km',
    gravity: '3.72 m/s² (0.379 g)',
    atmosphere: 'Thin CO₂ (~6.1 mbar)',
    tempRange: '143 K to 293 K (-130°C to +20°C)',
    missions: 'MGS (MOLA), Odyssey (THEMIS, GRS), MRO'
  },
  earth: {
    name: 'Earth (Terra)',
    role: 'Terrestrial Reference Baseline (128 Analog Sites)',
    radius: '6,371.0 km',
    gravity: '9.81 m/s² (1.000 g)',
    atmosphere: 'N₂/O₂ (1,013 mbar)',
    tempRange: '184 K to 330 K (-89°C to +57°C)',
    missions: 'Landsat, MODIS Terra/Aqua, GLiM, JRC Water'
  }
};

// Curated Earth Reference Sites (from 128-candidate catalog)
const CURATED_EARTH_SITES = [
  {
    id: 'earth_sudbury',
    name: 'Sudbury Impact Structure (Ontario, Canada)',
    body: 'earth',
    lat: 46.60,
    lon: -81.18,
    geology: 'Paleoproterozoic complex multi-ring impact crater with nickel-copper norite melt sheet.',
    primary_feature: 'Shatter cones, impact pseudotachylite, ancient eroded impact morphology.'
  },
  {
    id: 'earth_atacama',
    name: 'Atacama Desert / Yungay Basin (Chile)',
    body: 'earth',
    lat: -24.50,
    lon: -69.25,
    geology: 'Hyper-arid high-altitude nitrate and evaporite salt pan (Noachian Mars analog).',
    primary_feature: 'Extreme desiccation, perchlorate salts, minimal precipitation (< 1 mm/yr).'
  },
  {
    id: 'earth_death_valley',
    name: 'Death Valley Badlands (California, USA)',
    body: 'earth',
    lat: 36.53,
    lon: -116.93,
    geology: 'Sub-sea-level pull-apart tectonic basin with extreme diurnal temperature excursions.',
    primary_feature: 'High thermal inertia, alluvial fan slopes, evaporite salt flats.'
  },
  {
    id: 'earth_haughton',
    name: 'Haughton Impact Crater (Devon Island, Arctic)',
    body: 'earth',
    lat: 75.38,
    lon: -89.67,
    geology: 'High-latitude impact structure in permafrost continuous-ice regime (Mars polar analog).',
    primary_feature: 'Shatter cones, cryogenic hydrothermal pipes, patterned ground permafrost.'
  },
  {
    id: 'earth_mcmurdo',
    name: 'McMurdo Dry Valleys (Antarctica)',
    body: 'earth',
    lat: -77.50,
    lon: 162.50,
    geology: 'Cold-desert polar valleys with endorheic saline lakes and ventifact-sculpted basalt.',
    primary_feature: 'Cryogenic desert, permafrost ground ice, high UV radiation flux.'
  }
];

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initStarfieldCanvas();
  initIntroScreen();
  initShowcaseGlobes();
  initGlobe();
  initMap2D();
  initEarthMap();
  initRadarChart();
  initLocationSearch();
  updateEffectiveWeightsDisplay();
  selectPlanet('moon', false);
});

// Realistic 3D Earth Horizon & Real Scientific Telemetry Initialization
function initIntroScreen() {
  const introEl = document.getElementById('introScreen');
  if (!introEl) return;

  // Initialize Three.js Earth Horizon if available
  if (typeof createIntroEarthHorizon === 'function') {
    state.introHorizon = createIntroEarthHorizon('introEarthCanvas');
  }

  const pBar = document.getElementById('introProgressBar');
  const pctEl = document.getElementById('introStatusPct');
  const telemApi = document.getElementById('introTelemAPI');
  const telemCatalog = document.getElementById('introTelemCatalog');

  // Verify real API connectivity and analog catalog readiness
  fetch('/api/health')
    .then(res => res.json())
    .then(data => {
      if (pBar) pBar.style.width = '100%';
      if (pctEl) pctEl.textContent = '100% OPERATIONAL';
      if (telemApi) telemApi.textContent = `FastAPI v${data.version || '1.0'} Online (${data.status})`;
      if (telemCatalog && data.earth_analog_catalog_candidates) {
        telemCatalog.textContent = `${data.earth_analog_catalog_candidates} Analog Cells Cached`;
      }
    })
    .catch(err => {
      console.warn('API health check error:', err);
      if (pBar) pBar.style.width = '85%';
      if (pctEl) pctEl.textContent = 'LOCAL CACHE READY';
    });
}

function dismissIntroScreen() {
  const introEl = document.getElementById('introScreen');
  if (!introEl) return;
  introEl.classList.add('intro-fade-out');
  setTimeout(() => {
    introEl.classList.add('hidden');
    if (state.introHorizon && typeof state.introHorizon.destroy === 'function') {
      state.introHorizon.destroy();
      state.introHorizon = null;
    }
  }, 600);
}

// Quick Location Search
async function initLocationSearch() {
  const input = document.getElementById('locationSearchInput');
  const dropdown = document.getElementById('locationSearchDropdown');
  if (!input || !dropdown) return;

  // Build unified search database from Moon, Mars, and Earth targets
  let moonTargets = [];
  let marsTargets = [];
  try {
    const resMoon = await fetch('/api/targets?body=moon');
    const dMoon = await resMoon.json();
    moonTargets = (dMoon.targets || []).map(t => ({ ...t, body: 'moon' }));
  } catch(e) {}

  try {
    const resMars = await fetch('/api/targets?body=mars');
    const dMars = await resMars.json();
    marsTargets = (dMars.targets || []).map(t => ({ ...t, body: 'mars' }));
  } catch(e) {}

  const earthTargets = CURATED_EARTH_SITES.map(t => ({ ...t, body: 'earth' }));
  state.searchDatabase = [...moonTargets, ...marsTargets, ...earthTargets];

  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    if (!query) {
      dropdown.classList.add('hidden');
      dropdown.innerHTML = '';
      return;
    }

    const matches = (state.searchDatabase || []).filter(item => {
      const name = (item.name || '').toLowerCase();
      const geology = (item.geology || item.primary_feature || '').toLowerCase();
      const body = (item.body || '').toLowerCase();
      return name.includes(query) || geology.includes(query) || body.includes(query);
    }).slice(0, 8);

    if (matches.length === 0) {
      dropdown.innerHTML = '<div class="search-no-results">No matching planetary sites found</div>';
      dropdown.classList.remove('hidden');
      return;
    }

    dropdown.innerHTML = '';
    matches.forEach(item => {
      const opt = document.createElement('div');
      opt.className = 'search-result-item';
      const bColor = item.body === 'earth' ? '#38bdf8' : (item.body === 'mars' ? '#fba774' : '#cbd5e1');
      opt.innerHTML = `
        <div class="search-item-header">
          <span class="search-item-title">${item.name}</span>
          <span class="search-item-badge" style="color:${bColor}; border-color:${bColor}44">${item.body.toUpperCase()}</span>
        </div>
        <div class="search-item-desc">${item.geology || item.primary_feature || `${item.lat}°, ${item.lon}°`}</div>
      `;
      opt.onclick = () => {
        input.value = item.name;
        dropdown.classList.add('hidden');
        openExploreMode(item.body);
        onSiteSelected(item.id, true);
      };
      dropdown.appendChild(opt);
    });
    dropdown.classList.remove('hidden');
  });

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.add('hidden');
    }
  });
}

// Realistic 3D Showcase Globes for Landing Page Cards (Calibrated Visibility)
function initShowcaseGlobes() {
  if (typeof createShowcaseGlobe !== 'function') return;

  state.showcaseGlobes.earth = createShowcaseGlobe('canvasEarthShowcase', 'earth');
  state.showcaseGlobes.moon = createShowcaseGlobe('canvasMoonShowcase', 'moon');
  state.showcaseGlobes.mars = createShowcaseGlobe('canvasMarsShowcase', 'mars');
}

// Twinkling Space Canvas for Landing & Exploration Background
function initStarfieldCanvas() {
  const canvas = document.getElementById('starsCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  const numStars = 200;
  const stars = [];
  for (let i = 0; i < numStars; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      radius: Math.random() * 1.2 + 0.3,
      alpha: Math.random(),
      speed: Math.random() * 0.015 + 0.005
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const star of stars) {
      star.alpha += star.speed;
      const opacity = 0.25 + Math.sin(star.alpha) * 0.45;
      ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0.1, opacity)})`;
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }
  draw();
}

// ============================================================================
// Navigation & View Transitions
// ============================================================================
function showLanding() {
  document.getElementById('landingView').classList.remove('hidden');
  document.getElementById('explorationView').classList.add('hidden');
  closeComparisonDrawer();
}

function openExploreMode(body) {
  state.currentMode = 'explore';
  const pillExp = document.getElementById('navModeExplore');
  const pillCmp = document.getElementById('navModeCompare');
  if (pillExp) pillExp.classList.add('active');
  if (pillCmp) pillCmp.classList.remove('active');

  document.getElementById('landingView').classList.add('hidden');
  document.getElementById('comparisonDrawer').classList.add('hidden');
  document.getElementById('explorationView').classList.remove('hidden');

  if (body) {
    selectPlanet(body);
  } else if (!state.currentBody) {
    selectPlanet('moon');
  }

  setTimeout(() => {
    if (state.globe) state.globe.onResize();
    if (state.map2d) state.map2d.invalidateSize();
  }, 180);
}

function openCompareMode(body) {
  state.currentMode = 'compare';
  const pillExp = document.getElementById('navModeExplore');
  const pillCmp = document.getElementById('navModeCompare');
  if (pillCmp) pillCmp.classList.add('active');
  if (pillExp) pillExp.classList.remove('active');

  if (body) {
    if (body === 'earth') {
      selectPlanet('moon');
    } else {
      selectPlanet(body);
    }
  } else if (state.currentBody === 'earth') {
    selectPlanet('moon');
  }

  document.getElementById('landingView').classList.add('hidden');
  document.getElementById('explorationView').classList.add('hidden');
  document.getElementById('comparisonDrawer').classList.remove('hidden');

  // Update target banner & trigger match
  const bUpper = state.currentBody.toUpperCase();
  const badge = document.getElementById('consoleTargetBodyBadge');
  if (badge) badge.textContent = `${bUpper} TARGET (${state.currentBody === 'moon' ? 'LOLA' : 'MOLA'})`;

  const siteName = document.getElementById('targetTitleDisplay')?.textContent || `${bUpper} Target Site`;
  const nameEl = document.getElementById('consoleTargetName');
  if (nameEl) nameEl.textContent = siteName;

  const latSign = state.currentLat >= 0 ? 'N' : 'S';
  const lonSign = state.currentLon >= 0 ? 'E' : 'W';
  const coordsEl = document.getElementById('consoleTargetCoords');
  if (coordsEl) {
    coordsEl.textContent = `${Math.abs(state.currentLat).toFixed(2)}° ${latSign}, ${Math.abs(state.currentLon).toFixed(2)}° ${lonSign}`;
  }

  setTimeout(() => {
    if (state.earthMap) state.earthMap.invalidateSize();
  }, 200);

  runAnalogMatch();
}

function beginExploration(chosenBody) {
  openExploreMode(chosenBody);
}

// ============================================================================
// AREA 2: Planet Selection
// ============================================================================
function selectPlanet(body, triggerExtraction = true) {
  const cleanBody = body.toLowerCase();
  state.currentBody = cleanBody;

  // 1. Update Navigation Bar Pills
  ['moon', 'mars', 'earth'].forEach(b => {
    const btn = document.getElementById(`navBtn_${b}`);
    if (btn) {
      btn.className = `planet-pill ${b === cleanBody ? `active-${b}` : ''}`;
    }
  });

  // 2. Update Left Telemetry Panel
  const telem = PLANET_TELEMETRY[cleanBody] || PLANET_TELEMETRY.moon;
  document.getElementById('telemetryPlanetName').textContent = telem.name;
  document.getElementById('telemetryPlanetRole').textContent = telem.role;
  document.getElementById('telemRadius').textContent = telem.radius;
  document.getElementById('telemGravity').textContent = telem.gravity;
  document.getElementById('telemAtmosphere').textContent = telem.atmosphere;
  document.getElementById('telemTempRange').textContent = telem.tempRange;
  document.getElementById('telemMissions').textContent = telem.missions;

  // 3. Update 3D Globe Body
  if (state.globe) {
    state.globe.setBody(cleanBody);
  }

  // 4. Update 2D NASA Map Basemap
  updateMap2DLayer(cleanBody);

  // 5. Load Curated Sites for Selected Planet
  loadCuratedSites(cleanBody, triggerExtraction);
}

// ============================================================================
// AREA 3: 3D Planetary Globe Setup
// ============================================================================
function initGlobe() {
  const container = document.getElementById('globeContainer');
  if (!container || typeof PlanetaryGlobe === 'undefined') return;

  state.globe = new PlanetaryGlobe(container, {
    initialBody: state.currentBody,
    initialLat: state.currentLat,
    initialLon: state.currentLon,
    radius: 2.0,
    onLocationSelect: (lat, lon) => {
      onCoordinateSelected(lat, lon);
    }
  });
}

// ============================================================================
// NASA 2D Cartographic Map Setup (Leaflet)
// ============================================================================
function initMap2D() {
  const mapEl = document.getElementById('map2dContainer');
  if (!mapEl || typeof L === 'undefined') return;

  state.map2d = L.map('map2dContainer', {
    center: [state.currentLat, state.currentLon],
    zoom: 3,
    minZoom: 1,
    maxZoom: 7,
  });

  setupPlanetaryCoordinateGrid(state.map2d);
  updateMap2DLayer('moon');

  state.map2dMarker = L.marker([state.currentLat, state.currentLon], { draggable: true }).addTo(state.map2d);

  state.map2dMarker.on('dragend', function() {
    const c = state.map2dMarker.getLatLng();
    onCoordinateSelected(parseFloat(c.lat.toFixed(2)), parseFloat(c.lng.toFixed(2)));
  });

  state.map2d.on('click', function(e) {
    onCoordinateSelected(parseFloat(e.latlng.lat.toFixed(2)), parseFloat(e.latlng.lng.toFixed(2)));
  });
}

function setupPlanetaryCoordinateGrid(map) {
  if (state.planetaryGridLayer) {
    map.removeLayer(state.planetaryGridLayer);
  }
  state.planetaryGridLayer = L.layerGroup();

  // Parallels (-60 to +60 in 30 deg intervals)
  for (let lat = -60; lat <= 60; lat += 30) {
    const line = L.polyline([[lat, -180], [lat, 180]], {
      color: '#334155',
      weight: 1,
      dashArray: '4, 4',
      interactive: false
    });
    state.planetaryGridLayer.addLayer(line);
  }

  // Meridians (-180 to +180 in 60 deg intervals)
  for (let lon = -180; lon <= 180; lon += 60) {
    const line = L.polyline([[-90, lon], [90, lon]], {
      color: '#334155',
      weight: 1,
      dashArray: '4, 4',
      interactive: false
    });
    state.planetaryGridLayer.addLayer(line);
  }

  state.planetaryGridLayer.addTo(map);
}

function updateMap2DLayer(body) {
  if (!state.map2d) return;

  if (state.map2dTileLayer) {
    state.map2d.removeLayer(state.map2dTileLayer);
    state.map2dTileLayer = null;
  }

  let layerConfig;
  if (body === 'moon') {
    layerConfig = {
      url: 'https://trek.nasa.gov/tiles/Moon/EQ/LRO_LOLA_ClrShade_Global_128ppd_v04/1.0.0/default/default028mm/{z}/{y}/{x}.png',
      attribution: 'NASA / GSFC / LRO LOLA / Moon Trek',
      name: 'Moon LRO LOLA Elevation Shaded Relief'
    };
  } else if (body === 'mars') {
    layerConfig = {
      url: 'https://trek.nasa.gov/tiles/Mars/EQ/Mars_MGS_MOLA_ClrShade_merge_global_463m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg',
      attribution: 'NASA / JPL / USGS / Mars Trek (MGS MOLA)',
      name: 'Mars MGS MOLA Elevation Hillshade'
    };
  } else {
    layerConfig = {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors',
      name: 'Earth Cartographic Basemap'
    };
  }

  state.map2dTileLayer = L.tileLayer(layerConfig.url, {
    attribution: layerConfig.attribution,
    maxZoom: body === 'earth' ? 9 : 7,
    minZoom: 1,
    noWrap: false
  });

  state.map2dTileLayer.on('tileerror', function() {
    console.warn('NASA WMTS Tile Layer offline - displaying planetary coordinate grid fallback');
  });

  state.map2dTileLayer.addTo(state.map2d);
}

// ============================================================================
// View Mode Switching (3D Globe vs 2D NASA Map vs Split View)
// ============================================================================
function switchViewMode(mode) {
  state.viewMode = mode;
  const globeEl = document.getElementById('globeContainer');
  const map2dEl = document.getElementById('map2dContainer');

  ['3d', '2d', 'split'].forEach(m => {
    const btn = document.getElementById(`btnView_${m}`);
    if (btn) btn.className = `view-mode-btn ${m === mode ? 'active' : ''}`;
  });

  if (mode === '3d') {
    globeEl.style.display = 'block';
    globeEl.style.width = '100%';
    map2dEl.style.display = 'none';
    if (state.globe) state.globe.onResize();
  } else if (mode === '2d') {
    globeEl.style.display = 'none';
    map2dEl.style.display = 'block';
    map2dEl.style.width = '100%';
    if (state.map2d) state.map2d.invalidateSize();
  } else { // Split View
    globeEl.style.display = 'block';
    globeEl.style.width = '50%';
    map2dEl.style.display = 'block';
    map2dEl.style.width = '50%';
    map2dEl.style.left = '50%';
    if (state.globe) state.globe.onResize();
    if (state.map2d) state.map2d.invalidateSize();
  }
}

// ============================================================================
// Curated Sites & Coordinate Synchronization
// ============================================================================
async function loadCuratedSites(body, triggerExtraction = true) {
  const container = document.getElementById('curatedSitesList');
  container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.78rem; padding: 8px;">Loading mission reference sites...</div>';

  let sites = [];
  if (body === 'earth') {
    sites = CURATED_EARTH_SITES;
  } else {
    try {
      const res = await fetch(`/api/targets?body=${body}`);
      const data = await res.json();
      sites = data.targets || [];
    } catch (err) {
      console.error('Failed to fetch targets from API:', err);
      sites = [];
    }
  }

  state.targetsList = sites;
  renderCuratedSites(sites);

  if (sites.length > 0) {
    const initialSite = sites[0];
    onSiteSelected(initialSite.id, triggerExtraction);
  }
}

function renderCuratedSites(sites) {
  const container = document.getElementById('curatedSitesList');
  container.innerHTML = '';

  if (sites.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.78rem; padding: 8px;">No reference sites available.</div>';
    return;
  }

  sites.forEach((site) => {
    const chip = document.createElement('div');
    chip.className = 'site-chip';
    chip.id = `siteChip_${site.id}`;
    chip.onclick = () => onSiteSelected(site.id, true);

    chip.innerHTML = `
      <div class="site-chip-header">
        <span class="site-chip-name">${site.name}</span>
        <span class="site-chip-coords">${site.lat}°, ${site.lon}°</span>
      </div>
      <div class="site-chip-geology">${site.geology || site.primary_feature || ''}</div>
    `;
    container.appendChild(chip);
  });
}

function onSiteSelected(siteId, triggerExtraction = true) {
  const site = state.targetsList.find(s => s.id === siteId);
  if (!site) return;

  document.querySelectorAll('.site-chip').forEach(c => c.classList.remove('active'));
  const activeChip = document.getElementById(`siteChip_${siteId}`);
  if (activeChip) activeChip.classList.add('active');

  document.getElementById('targetTitleDisplay').textContent = site.name;
  document.getElementById('targetStratigraphyDisplay').textContent = site.geology || 'Geologic feature';

  onCoordinateSelected(site.lat, site.lon, triggerExtraction);
}

function onCoordinateSelected(lat, lon, triggerExtraction = true) {
  state.currentLat = lat;
  state.currentLon = lon;

  // 1. Update Input Fields
  document.getElementById('inputLat').value = lat;
  document.getElementById('inputLon').value = lon;

  // 2. Update HUD Coordinate Readout
  document.getElementById('hudCoordsDisplay').textContent = `LAT: ${lat.toFixed(2)}° | LON: ${lon.toFixed(2)}°`;

  // 3. Update 3D Globe Marker & Smooth Fly
  if (state.globe) {
    state.globe.setMarker(lat, lon);
    state.globe.flyTo(lat, lon, 600);
  }

  // 4. Update 2D NASA Map Marker & Pan
  if (state.map2d) {
    if (state.map2dMarker) state.map2dMarker.setLatLng([lat, lon]);
    state.map2d.panTo([lat, lon]);
  }

  // 5. Trigger Multi-Parameter Extraction
  if (triggerExtraction) {
    extractTargetTile(lat, lon);
  }
}

function handleManualCoordinateInput() {
  const lat = parseFloat(document.getElementById('inputLat').value);
  const lon = parseFloat(document.getElementById('inputLon').value);

  if (isNaN(lat) || lat < -90 || lat > 90) {
    alert('Invalid latitude: must be between -90.0 and +90.0');
    return;
  }
  if (isNaN(lon)) {
    alert('Invalid longitude: must be numeric');
    return;
  }

  document.getElementById('targetTitleDisplay').textContent = `Target Tile (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`;
  document.getElementById('targetStratigraphyDisplay').textContent = `Equal-Area 25 km Remote Sensing Analysis Cell on ${state.currentBody.toUpperCase()}`;

  onCoordinateSelected(lat, lon, true);
}

// ============================================================================
// Multi-Parameter Tile Extraction (/api/extract)
// ============================================================================
async function extractTargetTile(lat, lon) {
  const btn = document.getElementById('btnExtractTile');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Extracting Features...';
  }

  try {
    const res = await fetch('/api/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        body: state.currentBody,
        lat: lat,
        lon: lon
      })
    });

    if (!res.ok) {
      const err = await res.json();
      console.warn('Extraction API returned error:', err.detail);
      return;
    }

    const data = await res.json();
    state.extractedTile = data.tile;
    renderExtractedTileData(data.tile);
  } catch (err) {
    console.error('Extraction error:', err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        Extract Tile Features
      `;
    }
  }
}

function renderExtractedTileData(tile) {
  if (!tile) return;

  // 0. Update Location Overview Header Banner
  const bUpper = state.currentBody.toUpperCase();
  const badgeEl = document.getElementById('overviewBodyBadge');
  if (badgeEl) badgeEl.textContent = `${bUpper} SURFACE TARGET`;

  const coordsEl = document.getElementById('overviewLocationCoords');
  if (coordsEl) {
    const latSign = state.currentLat >= 0 ? 'N' : 'S';
    const lonSign = state.currentLon >= 0 ? 'E' : 'W';
    coordsEl.textContent = `${Math.abs(state.currentLat).toFixed(2)}° ${latSign}, ${Math.abs(state.currentLon).toFixed(2)}° ${lonSign}`;
  }

  const elevEl = document.getElementById('overviewLocationElevation');
  if (elevEl) {
    const elevStr = (tile.elevation_mean_m !== null && tile.elevation_mean_m !== undefined)
      ? (tile.elevation_mean_m >= 1000 || tile.elevation_mean_m <= -1000 ? (tile.elevation_mean_m / 1000).toFixed(2) + ' km' : tile.elevation_mean_m.toFixed(0) + ' m')
      : 'N/A';
    const reliefStr = (tile.relief_m !== null && tile.relief_m !== undefined) ? `${tile.relief_m.toFixed(0)} m` : 'N/A';
    elevEl.textContent = `${elevStr} (Relief: ${reliefStr})`;
  }

  const regionEl = document.getElementById('overviewLocationRegion');
  if (regionEl) {
    regionEl.textContent = tile.geology_stratigraphic_unit || 
      (state.currentBody === 'moon' ? 'Lunar Highlands / Mare Plain' : (state.currentBody === 'mars' ? 'Martian Volcanic / Cratered Terrain' : 'Terrestrial Geological Province'));
  }

  // 1. Terrain Geomorphometry
  const tValid = tile.terrain_valid;
  document.getElementById('badgeTerrain').className = `group-status-badge ${tValid ? 'badge-valid' : 'badge-unobserved'}`;
  document.getElementById('badgeTerrain').textContent = tValid ? '✓ OBSERVED' : '⚠️ N/A';
  document.getElementById('metricSlope').textContent = tValid && tile.slope_mean_deg !== null ? `${tile.slope_mean_deg.toFixed(2)}°` : 'N/A';
  document.getElementById('metricTRI').textContent = tValid && tile.tri_mean_m !== null ? `${tile.tri_mean_m.toFixed(1)} m` : 'N/A';
  document.getElementById('metricRelief').textContent = tValid && tile.relief_m !== null ? `${tile.relief_m.toFixed(0)} m` : 'N/A';
  document.getElementById('metricRes').textContent = tile.effective_res_km ? `${(tile.effective_res_km * 1000).toFixed(0)} m` : '~118 m';

  // 2. Mineralogy & Composition
  const mValid = tile.mineral_valid;
  document.getElementById('badgeMineral').className = `group-status-badge ${mValid ? 'badge-valid' : 'badge-unobserved'}`;
  document.getElementById('badgeMineral').textContent = mValid ? '✓ OBSERVED' : '⚠️ N/A';
  document.getElementById('metricFeO').textContent = mValid && tile.mineral_fe_wt_pct !== null ? `${tile.mineral_fe_wt_pct.toFixed(2)} wt%` : 'N/A (Uncalibrated)';
  document.getElementById('metricTiO2').textContent = mValid && tile.mineral_ti_wt_pct !== null ? `${tile.mineral_ti_wt_pct.toFixed(2)} wt%` : 'N/A (Uncalibrated)';

  // 3. Thermophysical Environment
  const thValid = tile.thermal_valid;
  document.getElementById('badgeThermal').className = `group-status-badge ${thValid ? 'badge-valid' : 'badge-unobserved'}`;
  document.getElementById('badgeThermal').textContent = thValid ? '✓ OBSERVED' : '⚠️ N/A';
  document.getElementById('metricDayTemp').textContent = thValid && tile.thermal_day_temp_k !== null ? `${tile.thermal_day_temp_k.toFixed(1)} K` : 'N/A';
  document.getElementById('metricNightTemp').textContent = thValid && tile.thermal_night_temp_k !== null ? `${tile.thermal_night_temp_k.toFixed(1)} K` : 'N/A';

  // 4. Water, Ice & Volatiles
  const vValid = tile.volatile_valid;
  document.getElementById('badgeVolatiles').className = `group-status-badge ${vValid ? 'badge-valid' : 'badge-unobserved'}`;
  document.getElementById('badgeVolatiles').textContent = vValid ? '✓ OBSERVED' : '⚠️ N/A';
  document.getElementById('metricWEH').textContent = vValid && tile.volatile_weh_wt_pct !== null ? `${tile.volatile_weh_wt_pct.toFixed(2)} wt%` : 'N/A';
  document.getElementById('metricPSR').textContent = tile.volatile_psr_area_fraction !== null && tile.volatile_psr_area_fraction !== undefined ? `${(tile.volatile_psr_area_fraction * 100).toFixed(1)}%` : 'N/A';

  // 5. Geological Context & Landforms
  const gValid = tile.geology_valid;
  document.getElementById('badgeGeology').className = `group-status-badge ${gValid ? 'badge-valid' : 'badge-unobserved'}`;
  document.getElementById('badgeGeology').textContent = gValid ? '✓ OBSERVED' : '⚠️ N/A';
  document.getElementById('metricCraterN1').textContent = tile.crater_density_n1 !== null && tile.crater_density_n1 !== undefined ? tile.crater_density_n1.toExponential(2) : 'N/A';
  document.getElementById('metricUnit').textContent = tile.geology_stratigraphic_unit || 'General Terrain';

  // 6. Atmospheric & Space Environment
  const atmoPress = document.getElementById('metricAtmPressure');
  const atmoGas = document.getElementById('metricAtmGas');
  const atmoSolar = document.getElementById('metricSolarFlux');
  const atmoRad = document.getElementById('metricRadiation');
  if (state.currentBody === 'moon') {
    if (atmoPress) atmoPress.textContent = '< 10⁻¹² bar (< 0.1 µPa)';
    if (atmoGas) atmoGas.textContent = 'Exosphere (He, Ne, H₂)';
    if (atmoSolar) atmoSolar.textContent = '1,361 W/m² (1.00 AU)';
    if (atmoRad) atmoRad.textContent = 'Unshielded (Cosmic / Solar)';
  } else if (state.currentBody === 'mars') {
    if (atmoPress) atmoPress.textContent = '~6.1 mbar (610 Pa)';
    if (atmoGas) atmoGas.textContent = '95.3% CO₂, 2.6% N₂, 1.9% Ar';
    if (atmoSolar) atmoSolar.textContent = '590 W/m² (1.52 AU)';
    if (atmoRad) atmoRad.textContent = 'Surface ~0.24 Gy/yr';
  } else {
    if (atmoPress) atmoPress.textContent = '1,013 mbar (101.3 kPa)';
    if (atmoGas) atmoGas.textContent = '78.1% N₂, 20.9% O₂, 0.9% Ar';
    if (atmoSolar) atmoSolar.textContent = '1,361 W/m² (TOA)';
    if (atmoRad) atmoRad.textContent = 'Magnetosphere Shielded';
  }

  let validCount = 0;
  if (tValid) validCount++;
  if (mValid) validCount++;
  if (thValid) validCount++;
  if (vValid) validCount++;
  if (gValid) validCount++;

  document.getElementById('safeguardValidCount').textContent = `${validCount} of 5`;
}

// ============================================================================
// PART B: Phase 2 Scientific Earth Analogs Comparison Console
// ============================================================================
function openComparisonDrawer() {
  if (state.currentBody === 'earth') {
    alert('TerraTwin compares extraterrestrial targets (Moon or Mars) to Earth analogs. Please select Moon or Mars.');
    return;
  }

  // Hide 3D exploration view and display comparison console overlay
  document.getElementById('explorationView').classList.add('hidden');
  document.getElementById('comparisonDrawer').classList.remove('hidden');

  // Update Target Header Banner in Research Console
  const bUpper = state.currentBody.toUpperCase();
  document.getElementById('consoleTargetBodyBadge').textContent = `${bUpper} TARGET (${state.currentBody === 'moon' ? 'LOLA' : 'MOLA'})`;
  
  const siteName = document.getElementById('targetTitleDisplay').textContent || `${bUpper} Target Site`;
  document.getElementById('consoleTargetName').textContent = siteName;

  const latSign = state.currentLat >= 0 ? 'N' : 'S';
  const lonSign = state.currentLon >= 0 ? 'E' : 'W';
  document.getElementById('consoleTargetCoords').textContent = 
    `${Math.abs(state.currentLat).toFixed(2)}° ${latSign}, ${Math.abs(state.currentLon).toFixed(2)}° ${lonSign}`;

  const resText = state.currentBody === 'moon'
    ? 'LRO LOLA ~118 m • LP-NS ~43 km footprint • Diviner 128 ppd'
    : 'MGS MOLA ~463 m • GRS ~600 km footprint • THEMIS ~100 m';
  document.getElementById('consoleTargetResolutions').textContent = resText;

  setTimeout(() => {
    if (state.earthMap) state.earthMap.invalidateSize();
  }, 200);

  runAnalogMatch();
}

function closeComparisonDrawer() {
  document.getElementById('comparisonDrawer').classList.add('hidden');
  document.getElementById('explorationView').classList.remove('hidden');

  setTimeout(() => {
    if (state.globe) state.globe.onResize();
  }, 180);
}

function updateEffectiveWeightsDisplay() {
  const axes = ['Terrain', 'Mineral', 'Thermal', 'Water', 'Geology'];
  let sum = 0;
  const raw = {};

  axes.forEach(axis => {
    const val = parseFloat(document.getElementById('w' + axis).value) || 0;
    raw[axis] = val;
    sum += val;
  });

  axes.forEach(axis => {
    const eff = sum > 0 ? ((raw[axis] / sum) * 100).toFixed(1) : '20.0';
    document.getElementById('effW' + axis).textContent = `Raw: ${raw[axis]} | Eff: ${eff}%`;
  });

  state.weights = {
    terrain: raw['Terrain'],
    mineral: raw['Mineral'],
    thermal: raw['Thermal'],
    water: raw['Water'],
    geology: raw['Geology']
  };
}

async function runAnalogMatch() {
  const btn = document.getElementById('btnRunMatchInDrawer');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>Evaluating 128 Candidates...</span>`;
  }

  const minCov = parseFloat(document.getElementById('drawerMinCov').value) / 100.0;
  state.minCoverage = minCov;

  try {
    const res = await fetch('/api/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        body: state.currentBody,
        lat: state.currentLat,
        lon: state.currentLon,
        weights: state.weights,
        top_k: 5,
        min_coverage: minCov,
        include_unqualified: true
      })
    });

    if (!res.ok) {
      const err = await res.json();
      alert('Match API error: ' + (err.detail || 'Failed to match analogs'));
      return;
    }

    const data = await res.json();
    state.rankedAnalogs = data.ranked_analogs || [];
    renderAnalogMatchResults(data);
  } catch (err) {
    console.error('Analog match query error:', err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"></polyline>
          <polyline points="1 20 1 14 7 14"></polyline>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
        </svg>
        <span>Re-Evaluate Global Analogs</span>
      `;
    }
  }
}

function renderAnalogMatchResults(data) {
  const list = document.getElementById('drawerAnalogsList');
  list.innerHTML = '';

  const analogs = data.ranked_analogs || [];
  const target = data.target || {};

  // 1. Update Target Observation Summary in Column 1
  let targetValidCount = 0;
  const targetGroups = [
    { key: 'terrain_valid', label: 'Terrain' },
    { key: 'mineral_valid', label: 'Mineral' },
    { key: 'thermal_valid', label: 'Thermal' },
    { key: 'volatile_valid', label: 'Volatiles' },
    { key: 'geology_valid', label: 'Geology' },
  ];

  const pillContainer = document.getElementById('consoleTargetGroupPills');
  if (pillContainer) {
    pillContainer.innerHTML = targetGroups.map(g => {
      const isValid = target[g.key] === true;
      if (isValid) targetValidCount++;
      return `<span class="${isValid ? 'pill-valid' : 'pill-unobserved'}">${isValid ? '✓' : '✗'} ${g.label}</span>`;
    }).join('');
  }
  document.getElementById('consoleObsCount').textContent = targetValidCount;
  document.getElementById('resultsCountBadge').textContent = `${analogs.length} Candidates Evaluated`;

  if (analogs.length === 0) {
    list.innerHTML = '<div style="color: var(--status-warning); padding: 16px;">No Earth candidates returned.</div>';
    return;
  }

  // 2. Clear previous Earth markers
  state.earthMarkers.forEach(m => state.earthMap.removeLayer(m));
  state.earthMarkers = [];
  const bounds = [];

  // 3. Render Ranked Analog Cards in Column 2
  analogs.forEach((a, idx) => {
    const card = document.createElement('div');
    card.className = `analog-card ${idx === state.selectedCandidateIndex ? 'active-inspected' : ''}`;
    card.id = `analogCard_${idx}`;
    card.onclick = () => inspectCandidate(idx);

    const isQualified = a.is_qualified_match;
    const scoreColor = isQualified ? 'var(--status-success)' : '#f87171';
    const qualBadge = isQualified
      ? `<span class="badge-qualified">✓ QUALIFIED MATCH</span>`
      : `<span class="badge-unqualified">⚠️ INSUFFICIENT COVERAGE</span>`;

    const noticeBox = !isQualified ? `
      <div class="unqualified-callout">
        <strong>Coverage Safeguard:</strong> Only <strong>${a.valid_groups_summary}</strong> (${a.composite_coverage_pct}% valid coverage &lt; ${a.min_coverage_threshold_pct}% threshold).<br>
        Score (<strong>${a.composite_similarity_pct}%</strong>) computed strictly from: <em>${a.observed_groups.join(', ')}</em>.<br>
        Unobserved groups (<em>${a.unobserved_groups.join(', ')}</em>) are marked N/A and excluded from composite similarity.
      </div>
    ` : '';

    card.innerHTML = `
      <div class="analog-header">
        <div>
          <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 3px;">
            <span class="analog-rank">#${a.rank}</span>
            ${qualBadge}
          </div>
          <span style="font-weight: 700; font-size: 0.95rem; color: #ffffff;">${a.name}</span>
          <div style="font-size: 0.73rem; color: var(--text-secondary); margin-top: 2px;">
            Lat: ${a.lat.toFixed(2)}°, Lon: ${a.lon.toFixed(2)}° | Category: ${a.analog_category}
          </div>
        </div>
        <div style="text-align: right;">
          <div class="analog-score" style="color: ${scoreColor};">${a.composite_similarity_pct}%</div>
          <div style="font-size: 0.68rem; color: var(--text-muted);">${isQualified ? 'Qualified Match' : 'Unqualified Match'}</div>
        </div>
      </div>

      <div style="font-size: 0.73rem; color: #94a3b8; display: flex; justify-content: space-between; background: #070d1c; padding: 4px 8px; border-radius: 4px;">
        <span>Observed: <strong>${a.valid_groups_summary}</strong></span>
        <span>Coverage: <strong>${a.composite_coverage_pct}%</strong> (Req: ${a.min_coverage_threshold_pct}%)</span>
      </div>

      ${noticeBox}

      <div style="margin-top: 2px;">
        ${renderScoreRow('Terrain', a.parameter_scores.terrain, a.parameter_coverage.terrain)}
        ${renderScoreRow('Mineralogy', a.parameter_scores.mineral, a.parameter_coverage.mineral)}
        ${renderScoreRow('Thermal', a.parameter_scores.thermal, a.parameter_coverage.thermal)}
        ${renderScoreRow('Volatiles', a.parameter_scores.water, a.parameter_coverage.water)}
        ${renderScoreRow('Geology', a.parameter_scores.geology, a.parameter_coverage.geology)}
      </div>

      <div class="analog-rationale">
        ${a.scientific_rationale}
      </div>

      <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); border-top: 1px solid var(--border-glass); padding-top: 6px;">
        <span>Mutual: ${a.observed_groups.join(', ') || 'None'}</span>
        <span style="color: #38bdf8; font-weight: 600;">Inspect Deep Profile ➔</span>
      </div>
    `;

    list.appendChild(card);

    // Marker on Earth Map
    if (a.lat !== undefined && a.lon !== undefined && state.earthMap) {
      const m = L.circleMarker([a.lat, a.lon], {
        radius: 6,
        color: isQualified ? '#10b981' : (idx === 0 ? '#f59e0b' : '#3b82f6'),
        fillColor: isQualified ? '#10b981' : (idx === 0 ? '#f59e0b' : '#3b82f6'),
        fillOpacity: 0.85
      }).addTo(state.earthMap);

      m.bindPopup(`<b>#${a.rank}: ${a.name}</b><br>Score: ${a.composite_similarity_pct}% (${isQualified ? 'Qualified' : 'Insufficient Coverage'})<br>${a.scientific_rationale}`);
      m.on('click', () => inspectCandidate(idx));
      state.earthMarkers.push(m);
      bounds.push([a.lat, a.lon]);
    }
  });

  if (bounds.length > 0 && state.earthMap) {
    state.earthMap.fitBounds(bounds, { padding: [30, 30] });
  }

  // 4. Default: Inspect #1 candidate
  inspectCandidate(0);
}

function inspectCandidate(idx) {
  if (!state.rankedAnalogs || !state.rankedAnalogs[idx]) return;
  state.selectedCandidateIndex = idx;
  const cand = state.rankedAnalogs[idx];

  // Highlight card in list
  document.querySelectorAll('.analog-card').forEach((c, i) => {
    if (i === idx) c.classList.add('active-inspected');
    else c.classList.remove('active-inspected');
  });

  // 1. Update Radar Profile Header
  document.getElementById('radarCandidateTag').textContent = `#${cand.rank} ${cand.name}`;

  // 2. Update 5-Axis Radar Chart
  if (cand.radar_profile && state.radarChart) {
    state.radarChart.data.datasets[0].data = cand.radar_profile.values;
    state.radarChart.data.datasets[0].label = `#${cand.rank} ${cand.name}`;
    state.radarChart.update();

    const pillContainer = document.getElementById('drawerRadarPills');
    if (pillContainer) {
      const axes = cand.radar_profile.axes;
      const vals = cand.radar_profile.values;
      const valids = cand.radar_profile.valid;
      pillContainer.innerHTML = axes.map((axis, i) => {
        const isValid = valids[i];
        const val = vals[i];
        if (isValid && val !== null && val !== undefined) {
          return `<span class="pill-valid">✓ ${axis}: ${val.toFixed(0)}%</span>`;
        } else {
          return `<span class="pill-unobserved" title="Unobserved">✗ ${axis}: N/A</span>`;
        }
      }).join('');
    }
  }

  // 3. Update 5-Group Side-by-Side Comparison Matrix
  const matrixContainer = document.getElementById('candidateGroupsMatrix');
  if (matrixContainer) {
    const groups = [
      {
        name: 'Terrain Geomorphometry',
        icon: '⛰️',
        score: cand.parameter_scores.terrain,
        valid: cand.parameter_coverage.terrain,
        targetNote: state.extractedTile ? `Slope ${state.extractedTile.slope_mean_deg ? state.extractedTile.slope_mean_deg.toFixed(1) + '°' : 'N/A'}` : 'Target Terrain',
        candNote: `Relief / Slope match`
      },
      {
        name: 'Mineralogy & Composition',
        icon: '🔬',
        score: cand.parameter_scores.mineral,
        valid: cand.parameter_coverage.mineral,
        targetNote: state.extractedTile ? (state.extractedTile.mineral_fe_wt_pct ? `FeO ${state.extractedTile.mineral_fe_wt_pct.toFixed(1)} wt%` : 'Uncalibrated') : 'Target Mineral',
        candNote: 'GLiM Lithology'
      },
      {
        name: 'Thermophysical Environment',
        icon: '🌡️',
        score: cand.parameter_scores.thermal,
        valid: cand.parameter_coverage.thermal,
        targetNote: state.extractedTile ? (state.extractedTile.thermal_day_temp_k ? `Day ${state.extractedTile.thermal_day_temp_k.toFixed(0)} K` : 'N/A') : 'Target Thermal',
        candNote: 'MODIS LST Day/Night'
      },
      {
        name: 'Water, Ice & Volatiles',
        icon: '💧',
        score: cand.parameter_scores.water,
        valid: cand.parameter_coverage.water,
        targetNote: state.extractedTile ? `WEH ${state.extractedTile.volatile_weh_wt_pct ? state.extractedTile.volatile_weh_wt_pct.toFixed(2) + ' wt%' : 'N/A'}` : 'Target Volatiles',
        candNote: 'JRC / Glaciers'
      },
      {
        name: 'Geological Context',
        icon: '💥',
        score: cand.parameter_scores.geology,
        valid: cand.parameter_coverage.geology,
        targetNote: state.extractedTile ? (state.extractedTile.geology_stratigraphic_unit || 'Stratigraphy') : 'Target Geology',
        candNote: 'PASSC Impacts / Context'
      }
    ];

    matrixContainer.innerHTML = groups.map(g => {
      let statusPill = '';
      if (!g.valid || g.score === null || g.score === undefined) {
        statusPill = `<span class="pill-unobserved">UNOBSERVED</span>`;
      } else if (g.score >= 70) {
        statusPill = `<span class="pill-valid">MATCHED (${g.score.toFixed(0)}%)</span>`;
      } else {
        statusPill = `<span class="badge-unqualified" style="font-size:0.65rem;">DIVERGENT (${g.score.toFixed(0)}%)</span>`;
      }

      return `
        <div class="matrix-group-item">
          <div class="matrix-group-header">
            <span>${g.icon} ${g.name}</span>
            ${statusPill}
          </div>
          <div class="matrix-subvals-row">
            <div class="matrix-subval-box">
              <div class="matrix-subval-lbl">Target Parameter</div>
              <div class="matrix-subval-num">${g.targetNote}</div>
            </div>
            <div class="matrix-subval-box">
              <div class="matrix-subval-lbl">Candidate Metric</div>
              <div class="matrix-subval-num">${g.candNote}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // 4. Pan Earth map to candidate coordinates
  if (state.earthMap && cand.lat !== undefined && cand.lon !== undefined) {
    state.earthMap.setView([cand.lat, cand.lon], 4);
  }
}

function renderScoreRow(label, score, isValid) {
  if (!isValid || score === null || score === undefined) {
    return `
      <div class="score-row">
        <span style="width: 80px; color: #94a3b8;">${label}</span>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width: 0%; background: #475569;"></div></div>
        <span style="color: #94a3b8; font-size: 0.7rem; font-style: italic;">N/A (Unobserved)</span>
      </div>
    `;
  }
  return `
    <div class="score-row">
      <span style="width: 80px; font-weight: 500;">${label}</span>
      <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${score}%;"></div></div>
      <span style="font-weight: 600; color: #38bdf8; font-family: var(--font-mono);">${score.toFixed(1)}%</span>
    </div>
  `;
}

// 5-Axis Radar Chart Setup
function initRadarChart() {
  const canvas = document.getElementById('drawerRadarChart');
  if (!canvas || typeof Chart === 'undefined') return;

  state.radarChart = new Chart(canvas.getContext('2d'), {
    type: 'radar',
    data: {
      labels: ['Terrain', 'Mineralogy', 'Thermal', 'Volatiles', 'Geology'],
      datasets: [{
        label: 'Candidate Similarity (%)',
        data: [null, null, null, null, null],
        backgroundColor: 'rgba(56, 189, 248, 0.22)',
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        pointRadius: 3.5,
        pointBackgroundColor: '#bae6fd',
        spanGaps: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { stepSize: 25, color: '#94a3b8', backdropColor: 'transparent', font: { family: 'JetBrains Mono', size: 9 } },
          grid: { color: 'rgba(56, 189, 248, 0.14)' },
          angleLines: { color: 'rgba(56, 189, 248, 0.14)' },
          pointLabels: { color: '#f8fafc', font: { size: 11, weight: '600', family: 'Inter' } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw;
              if (val === null || val === undefined) return `${context.label}: N/A (Missing data)`;
              return `${context.label}: ${val.toFixed(1)}% match`;
            }
          }
        }
      }
    }
  });
}

function initEarthMap() {
  const mapEl = document.getElementById('earthMap');
  if (!mapEl || typeof L === 'undefined') return;

  state.earthMap = L.map('earthMap', {
    center: [20.0, 0.0],
    zoom: 1,
    minZoom: 1,
    maxZoom: 8
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    noWrap: false
  }).addTo(state.earthMap);
}
