# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portfolio Optimization is a full-stack application for optimizing offshore renewable energy portfolios across wind, wave, and ocean current (kite) technologies on the US East Coast. It uses mathematical optimization (Gurobi/Pyomo) to maximize generation subject to LCOE (Levelized Cost of Energy) constraints and transmission limitations.

## Architecture

### High-Level Design
- **Frontend**: Next.js 14 (React 18, TypeScript) - interactive UI for portfolio configuration and visualization
- **Backend**: Flask (Python 3.11) - REST API for optimization computations
- **Deployment**: Docker Compose orchestration of both services
- **Communication**: Axios HTTP client calling Flask API (http://localhost:4000)

### Frontend Structure (`frontend/`)
**Technology Stack**: Next.js 14, React 18, TypeScript, Tailwind CSS, Headless UI

**Key Pages**:
- `/` - Landing page title
- `/prototype` - Main application interface with portfolio configuration form
- `/about/wind` - Wind technology details
- `/about/kite` - Ocean kite technology details

**Components** (`src/components/`):
- Input form components: `Input`, `MoneyInput`, `ResourceSelect`, `TransmissionCapSelect`, `YearSelect`
- UI utilities: `Navbar`, `Layout`, `PercentLoader`, `DownloadCard`

**API Client** (`src/api.js`):
Central Axios-based client managing all backend communication. Endpoints include:
- `test` - Service health check
- `resourceUpload` - Upload custom resource data files
- `generateWindBinaries` - Pre-process wind turbine performance data
- `windInputGeneration` - Aggregate wind data across time/space resolutions
- `kiteInputGeneration` - Process ocean current kite performance data
- `waveInputGeneration` - Process wave energy data
- `portfolioOptimization` - Main optimization solver
- `portfolioPlots` - Generate visualization outputs

**Configuration**:
- `next.config.mjs`: Uses standalone output mode for Docker
- `tsconfig.json`: Path alias `@/*` → `src/*`
- `tailwind.config.ts`: Includes Tremor charting library
- ESLint: Relaxed rules (no-unused-vars disabled, no-explicit-any allowed)

### Backend Structure (`backend/`)
**Technology Stack**: Flask, Python 3.11, Gurobi/Pyomo (optimization), NumPy/Pandas/GeoPandas (scientific computing)

**Core Modules**:
- `app.py` - Flask API server (port 4000) with CORS enabled
- `Port_Opt_MaxGeneration_EastCoast.py` - Main optimization engine using Pyomo/Gurobi
  - `SolvePortOpt_MaxGen_LCOE_Iterator()` - Solves optimization for multiple LCOE targets
  - `PreparePotOptInputs()` - Loads and validates input resources
  - Generates plots: efficient frontier, stacked costs, generation timeseries, deployment maps
- `*_EastCoast.py` - Technology-specific tools:
  - `WindTurbineTools_EastCoast.py` - Wind performance/cost calculations
  - `WaveDeviceTools_EastCoast.py` - Wave energy resource processing
  - `KiteFunctions_EastCoast.py` - Ocean kite power/cost models
  - `GeneralGeoTools_EastCoast.py` - Geospatial operations, plotting
  - `TransmissionTools_EastCoast.py` - Transmission system modeling
- `Port_Opt_Tools.py` - Utility functions for overlap detection
- `GetIdxInOutRadious.py` - Geographic filtering within collection radius

**Data Organization**:
- `InputData/` - Base resource/technology data (Wind, Transmission, CoastLine)
- `Tech Designs/` - Technology performance specifications (Wind, Wave, Current, Coaxial, Tidal)
- `OutputData/` - Generated outputs:
  - `Portfolios/` - Optimization results (.npz binary files)
  - `Plots/Portfolios/` - Generated visualizations
  - `Wind/`, `Wave/`, `OceanCurrent/` - Pre-processed resource data

**Key Dependencies**:
- `gurobipy`: Commercial optimization solver (requires license in `/gurobi.lic`)
- `pyomo`: Mathematical optimization modeling
- `geopandas/shapely/fiona`: Geospatial analysis
- `xarray/netcdf4`: Multi-dimensional gridded data
- `matplotlib`: Visualization

### Data Flow
1. User selects turbine designs, LCOE range, spatial/temporal parameters in UI
2. Frontend calls `/generateWindBinaries`, `/windInputGeneration`, etc. to pre-process resources
3. Frontend calls `/portfolioOptimization` with configuration
4. Backend loads design/resource files, solves multiple optimization problems (one per LCOE target)
5. Results stored as `.npz` files in `OutputData/Portfolios/` with naming scheme: `{transmission}${wind}${kite}${wave}${coaxial}$max={lcoe_max}$min={lcoe_min}$step={lcoe_step}`
6. Frontend requests `/portfolioPlots` to generate visualizations and download results

## Commands

### Development
```bash
# Start both services with live reload (requires Docker)
./dev.sh

# Start without live reload
./run.sh
```

### Frontend
```bash
cd frontend

# Development server (http://localhost:3000)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint TypeScript/React code
npm run lint
```

### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run Flask server (http://localhost:4000)
python app.py
```

### Docker
```bash
# Build images
docker compose build

# Run services (frontend on 3000, Flask on 4000)
docker compose up

# Stop services
docker compose down
```

## Environment Configuration

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API endpoint (default: `http://localhost:4000`)
- Set in `compose.yml` for Docker deployments

### Backend
- Gurobi license file expected at `/root/gurobi.lic` in Docker container (mounted from `./gurobi.lic`)
- NREL HSDS API credentials in `compose.yml`:
  - `hs_api_key`: NREL API key
  - `hs_bucket`: NREL dataset bucket
  - `hsds_endpoint`: NREL HDF5 service endpoint

## Important Notes

### Optimization Model Constraints
- **Objective**: Maximize total generation
- **LCOE Constraint**: Portfolio LCOE ≤ specified target
- **Transmission**: Limited by capacity and collection radius
- **Turbine Placement**: Maximum turbines per geographic site
- **Design Choices**: Select from predefined turbine designs

### File Path Handling
Backend uses forward slashes in file paths (e.g., `Wind/GenCost_Turbine.npz`). Portfolio names use `$` as delimiter to encode configuration: design choices are extracted from `.npz` filenames and rejoined with `#` in composite names.

### Caching
Pre-computed resource binaries (`.npz` files) are cached in `OutputData/`. Backend checks if files exist before recomputing—delete cache to force regeneration.

### Docker Setup
- Both services must be rebuilt after code changes (`docker compose build`)
- Frontend relies on `NEXT_PUBLIC_API_URL` environment variable for API routing
- Backend requires Gurobi license file mounted and visible

## Key Optimization Parameters
- `LCOE_RANGE`: Target cost range for portfolio ($/MWh), iterated by optimization solver
- `Max_CollectionRadious`: Geographic limit for turbine deployment (km)
- Turbines per site: `WindTurbinesPerSite`, `KiteTurbinesPerSite`, `WaveTurbinesPerSite`
- Cost scaling factors (in `Port_Opt_MaxGeneration_EastCoast.py`): `windCostScaling`, `kiteCostScaling`, `transmissionCostScaling` (sensitivity analysis levers)
