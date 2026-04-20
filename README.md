# LeadGen Pro

LeadGen Pro is a production-ready SaaS MVP for global lead generation and client acquisition for web/app development agencies.

## Tech Stack

- Backend: FastAPI, Pydantic, async `httpx`, `requests`, `BeautifulSoup`
- Frontend: React (Vite), Tailwind CSS
- External API: Google Places API (Text Search + Details)

## Project Structure

```text
backend/
  app/
    main.py
    api/
    services/
    models/
    schemas/
    core/
    utils/
frontend/
  src/
    components/
    pages/
    services/
    hooks/
    layouts/
```

## Backend Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
```

Set `GOOGLE_API_KEY` or `GOOGLE_PLACES_API_KEY` in `backend/.env`.

4. Run backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Configure environment:

```bash
cp .env.example .env
```

3. Run frontend:

```bash
npm run dev
```

Frontend URL:
- App: `http://localhost:5173`

Frontend API behavior:
- Local development defaults to `http://localhost:8000`
- Production defaults to relative `/api` calls, which is Vercel-friendly

## API Endpoints

- `GET /leads/search?city=<city>&type=<businessType>&country=<optionalCountry>`
- `GET /leads/export?city=<city>&type=<businessType>&country=<optionalCountry>`

## Vercel Deployment

LeadGen Pro is configured so the frontend deploys as a Vite static site and the FastAPI backend runs as a Vercel Python serverless function.

### Deployment Structure

```text
api/
  index.py            # Vercel serverless FastAPI entrypoint
backend/
  app/
    main.py           # Existing FastAPI application
frontend/
  dist/               # Vite production build output
vercel.json           # Vercel build + routing config
package.json          # Root build script for frontend
requirements.txt      # Root Python deps for Vercel
```

### Files Added for Vercel

- `api/index.py`
  - imports the existing FastAPI app from `backend/app/main.py`
  - exposes the top-level `app` ASGI instance for Vercel's Python runtime
- `vercel.json`
  - builds the frontend from `frontend/`
  - lets Vercel serve Python functions from `api/` using its native routing
- `requirements.txt`
  - mirrors the backend Python dependencies for Vercel builds
- `.python-version`
  - pins Python 3.12 so local and Vercel runtimes stay aligned

### Local Verification Before Deploy

1. Build the frontend:

```bash
cd frontend
npm install
npm run build
```

2. Run the backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Vercel Environment Variables

Set these in the Vercel dashboard for the project:

- `GOOGLE_API_KEY` or `GOOGLE_PLACES_API_KEY`
- `OPENAI_API_KEY`
- `FRONTEND_ORIGIN`
- `LEAD_MAX_RESULTS`
- `SCRAPER_TIMEOUT_SECONDS`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USER`
- `EMAIL_PASS`
- `GEODB_API_KEY`
- `GEODB_API_HOST`
- `GEODB_COUNTRIES_URL`
- `GEODB_CITIES_URL`

Notes:
- Use `FRONTEND_ORIGIN=https://lead-gen-pro-mu.vercel.app`
- `OPENAI_API_KEY` is safe to configure now even though the current app does not yet require it at runtime
- Keep `LEAD_MAX_RESULTS` between `10` and `15` for Vercel-friendly response times
- Set `SCRAPER_TIMEOUT_SECONDS=5` to keep scraping under serverless limits
- Enable "Automatically expose System Environment Variables" so preview and production URLs are added to the CORS allowlist automatically

### Deploy to Vercel

1. Push the repo to GitHub.
2. Import the repository into Vercel.
3. Keep the project root as the repository root.
4. Vercel will:
   - run `npm install --prefix frontend`
   - run the root `build` script
   - publish `frontend/dist`
   - deploy `api/index.py` as a Python serverless function
5. Add the environment variables in the Vercel dashboard.
6. Redeploy after saving env vars.

### Production Request Paths

Frontend requests are Vercel-safe and use:

- `/api/leads/search`
- `/api/leads/export`
- `/api/locations/autocomplete`
- `/api/locations/popular`
- `/api/locations/details`
- `/api/outreach/send-email`

### Important Serverless Notes

- Website scraping and enrichment should stay fast; keep request timeouts low.
- Avoid long-running tasks in request/response cycles.
- `/health` is exposed directly in local development and under `/api/health` on Vercel.
- If AI or bulk enrichment becomes heavier later, move that work to a queue/background job system.

## Core Business Rules

- Email extraction is attempted from:
  - website homepage
  - `/contact`
  - `/about`
- Priority score:
  - `HIGH`: missing website OR missing phone OR missing email
  - `MEDIUM`: weak website (missing title/meta tags)
  - `LOW`: website + phone + email are all available
- Data quality:
  - duplicate businesses are removed
  - city/country mismatch results are filtered

## Frontend Dashboard

- Premium SaaS table layout with:
  - Email column
  - Priority badges (`HIGH`, `MEDIUM`, `LOW`)
  - loading spinner
- Filters:
  - High Priority
  - Has Email
  - No Website
- KPI cards:
  - Total Leads
  - High Priority Leads
  - Emails Found

## Scalability Hooks

- `app/services/analyzer.py` is included as a placeholder for:
  - AI lead analysis
  - lead scoring
  - CRM enrichment
