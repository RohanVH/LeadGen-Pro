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

Set `GOOGLE_PLACES_API_KEY` in `backend/.env`.

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

## API Endpoints

- `GET /leads/search?city=<city>&type=<businessType>&country=<optionalCountry>`
- `GET /leads/export?city=<city>&type=<businessType>&country=<optionalCountry>`

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
