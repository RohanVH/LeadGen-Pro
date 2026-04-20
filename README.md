# LeadGen Pro

### AI-Powered Client Acquisition Platform

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/AI-OpenAI-412991?logo=openai&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini-4285F4?logo=google&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-22c55e)
![License](https://img.shields.io/badge/License-See%20LICENSE-lightgrey)

---

## 🚀 Overview

- Discover businesses globally with guided, intelligent search.
- Enrich every lead with contact, website, reviews, and social presence.
- Analyze each lead using AI to uncover needs, risks, and sales opportunities.
- Generate actionable recommendations so teams close clients faster.

---

## 🎯 Why This Project

Manual lead generation is slow, repetitive, and inconsistent.  
Cold outreach without context leads to poor conversion.

**LeadGen Pro solves this with AI-first lead intelligence.**

- Smart enrichment and prioritization
- Dynamic AI insights and chat assistance
- Targeted outreach guidance per business

---

## ✨ Features

### 🔍 Lead Discovery
- Global city + country search with category and business subtype flow
- Dynamic subtype suggestions with manual override support
- Smart pagination with load more + auto-load on scroll
- Duplicate prevention and location-aware filtering

### 🧠 AI Business Intelligence
- AI-generated business summary, strengths, weaknesses, and sentiment
- Outreach recommendation (`contact`/`skip`) and pitch suggestion
- On-demand lead analysis per row from the table
- Real-time fallback routing to keep insights available

### 💬 AI Assistant
- Per-lead modal assistant for interactive Q&A
- Conversation-aware responses using lead context
- Live thinking/loading states for smooth UX
- Designed for sales objections, positioning, and close strategy

### 📊 Data Enrichment
- Website content extraction and quality assessment
- Email discovery with source and confidence scoring
- Google rating/review ingestion
- Instagram and YouTube discovery support

### 🔁 AI Router (OpenAI + Gemini)
- Primary provider: OpenAI
- Secondary provider: Gemini
- Rule-based fallback if providers fail
- Normalized output format across providers

### 📈 Pagination System
- Offset/limit backend pagination with `hasMore`
- Frontend lead accumulation without replacing existing data
- Loaded progress visibility (`Loaded X / Y leads`)
- Stable filters and UI state while appending data

---

## 🖼️ Demo / Screenshots

![Dashboard Screenshot](./assets/dashboard.png)

---

## 🏗️ Tech Stack

### Frontend
![React](https://img.shields.io/badge/React-20232A?logo=react)
![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-06B6D4?logo=tailwindcss&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white)

### AI
![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-4285F4?logo=google&logoColor=white)

### Deployment
![Vercel](https://img.shields.io/badge/Vercel-000000?logo=vercel&logoColor=white)

---

## ⚙️ Setup

### 1) Clone
```bash
git clone <your-repo-url>
cd "LeadGen Pro"
```

### 2) Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## 🔐 Env Variables

```env
# Core
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:5173

# Data Providers
GOOGLE_PLACES_API_KEY=your_google_key
GEODB_API_KEY=your_geodb_key

# AI Providers
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash

# AI & Scraping
AI_MAX_LEADS=12
AI_BATCH_SIZE=4
SCRAPER_TIMEOUT_SECONDS=6
SCRAPER_MAX_CONCURRENCY=6
```

---

## 🧠 How It Works

**Search -> Fetch -> Enrich -> Analyze -> Recommend -> Contact**

1. User searches by category, subtype, and location.
2. System fetches business candidates from external data sources.
3. Pipeline enriches leads with website, email, reviews, and social data.
4. AI analyzes each lead to identify opportunities and risks.
5. Platform recommends what to sell and whether to contact.
6. Team launches outreach with smarter context and better timing.

---

## 💰 Use Cases

- **Freelancers** who need qualified leads without manual prospecting.
- **Agencies** that want AI-driven targeting and pitch precision.
- **Sales teams** seeking conversion-focused outbound workflows.

---

## 🛣️ Roadmap

- [ ] CRM system
- [ ] Outreach automation
- [ ] Multi-user support

---

## 👤 Author

**Rohan**

---

## ⚡ Final Note

**This is not just a tool — it's a client acquisition engine.**
