# TerraTwin Frontend

Interactive 3D Planetary Cartography and Comparative Planetary Science Interface for the **TerraTwin** platform.

## Architecture & Tech Stack

- **3D Celestial Cartography**: [Three.js](https://threejs.org/) + `OrbitControls` with physically calibrated ACES tone mapping, dynamic solar illumination, and raycasted spherical surface coordinate selection.
- **2D Cartographic Engine**: [Leaflet](https://leafletjs.com/) with NASA Trek WMTS mosaics (LRO LOLA for Moon, MGS MOLA for Mars) and global terrestrial basemaps.
- **Multidimensional Analysis**: [Chart.js](https://www.chartjs.org/) 5-axis radar profile visualization featuring scientific gap indicators for unobserved parameter groups.
- **Scientific Styling**: Responsive, aerospace-grade HUD styled with custom CSS3 animations (atmospheric scattering, cosmic drift, holographic callout rays).

## Directory Structure

```text
frontend/
├── public/
│   ├── assets/           # UI graphics and static branding assets
│   └── textures/         # Global planetary textures (Earth, Moon, Mars, Cosmic Nebula)
├── src/
│   ├── components/       # UI components (PlanetaryGlobe, RadarProfile)
│   ├── services/         # API client service layer (ApiService)
│   ├── styles/           # Aerospace UI stylesheets (terratwin.css)
│   └── app.js            # Main application state machine & controller
├── index.html            # Single-page dashboard entry point
├── package.json          # Node package definition
├── vite.config.js        # Vite development server configuration
└── README.md
```

## Running the Frontend

### Method A: Direct FastAPI Integration (Recommended)
The FastAPI backend serves the frontend automatically at root `/`:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### Method B: Vite Development Server
If you prefer developing with a standalone Vite live-reload server:
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000). API requests to `/api` and assets `/static` are automatically proxied to `http://127.0.0.1:8000`.
