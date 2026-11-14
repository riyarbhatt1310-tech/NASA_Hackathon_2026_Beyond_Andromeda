# Contributing to TerraTwin

Thank you for your interest in contributing to **TerraTwin**! We welcome contributions from planetary scientists, aerospace engineers, geospatial data analysts, and open-source developers.

---

## Code of Conduct

We are committed to providing a welcoming, collaborative, and inclusive environment. Please communicate constructively and treat fellow contributors with respect.

---

## Development Workflow

1. **Fork & Clone**:
   ```powershell
   git clone https://github.com/riyarbhatt1310-tech/NASA_Hackathon_2026_Beyond_Andromeda.git
   cd NASA_Hackathon_2026_Beyond_Andromeda
   ```

2. **Branching Strategy**:
   Create a focused feature branch from `main`:
   ```powershell
   git checkout -b feature/my-new-feature
   ```

3. **Environment Setup**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   pip install pytest pytest-cov httpx
   ```

4. **Running the Applications**:
   - Backend API:
     ```powershell
     python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
     ```
   - Frontend (via Vite):
     ```powershell
     cd frontend
     npm install
     npm run dev
     ```

5. **Testing & Validation**:
   All contributions must pass the automated test suite without regressions:
   ```powershell
   pytest -v
   ```

6. **Submitting Changes**:
   - Commit with clear, descriptive messages following [Conventional Commits](https://www.conventionalcommits.org/).
   - Push to your fork and submit a Pull Request against `main`.
   - Describe the scientific rationale or functional improvements in detail.

---

## Scientific Contribution Guidelines

- **Missing Data Governance**: Never assign arbitrary zero values to missing or unobserved remote sensing layers. Maintain `None` / `NaN` semantics.
- **Coverage Safeguard**: Ensure matches maintain the minimum 60% mutually observed valid coverage threshold.
- **Physical Bounds**: Verify all calculations conform to physical realities (e.g. slopes $\in [0, 90]^\circ$, TRI $\ge 0$, positive thermal inertia).
- **Coordinate Systems**: Adhere strictly to IAU 2000 planetocentric coordinate frames for extraterrestrial bodies and WGS84 for Earth.
