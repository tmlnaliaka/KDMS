# KDMS — Kenya Disaster Management System

A real-time disaster monitoring platform for Kenya's NDMA, powered by **Gemini 1.5 Flash**, **FastAPI**, **React**, and **Leaflet**.

---

## 🚀 Quick Start

### 1. Clone & Configure

```bash
cd kdms
cp .env.template .env
# Fill in your API keys in .env
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python seed_data.py        # Seeds 47 counties, workers, refuge sites
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at: **http://localhost:5173**

---

## 🔑 API Keys Required (all free tiers)

| Key | Where to get it |
|-----|----------------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `OPENWEATHER_API_KEY` | [openweathermap.org](https://openweathermap.org/api) — free 1,000 calls/day |
| `AFRICASTALKING_USERNAME` | `sandbox` (free testing) |
| `AFRICASTALKING_API_KEY` | [africastalking.com](https://africastalking.com) sandbox |
| `NASA_FIRMS_MAP_KEY` | [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov/api/area/) |

> **System works without keys** — mock data and fallback responses are built in.

---

## 🏗️ Architecture

```
kdms/
├── backend/
│   ├── main.py           # FastAPI — 8 REST endpoints
│   ├── database.py       # SQLite + async helpers
│   ├── seed_data.py      # 47 counties, workers, refuge sites
│   ├── data_sources.py   # OpenWeatherMap, USGS, NASA FIRMS, Open-Meteo
│   ├── gemini_service.py # 4 AI jobs (risk, predict, SMS, report)
│   ├── sms_service.py    # Africa's Talking SMS
│   ├── scheduler.py      # APScheduler — polls APIs every 30 min
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx         # Shell + sidebar + router
        ├── MapView.jsx     # Leaflet disaster map
        ├── RiskPanel.jsx   # 47 county risk score cards
        ├── WorkerPanel.jsx # Worker dispatch console
        ├── AlertConsole.jsx# SMS alert sender
        └── AIReport.jsx    # AI situation report + 72hr predictions
```

## 🤖 Gemini AI Jobs

| Job | Trigger | Output |
|-----|---------|--------|
| Risk Scoring | Every 30 min | Score per county (0–100) |
| 72hr Prediction | On demand | County threat forecasts |
| SMS Alert | On demand | English + Swahili under 160 chars |
| National SitRep | On demand | Formatted markdown briefing |

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/disasters` | All disasters (filter with `?status=active`) |
| GET | `/counties/risk` | Risk score for all 47 counties |
| POST | `/report` | Field worker submits disaster |
| POST | `/dispatch` | Assign worker to disaster |
| POST | `/alert/send` | AI-generate & send SMS |
| GET | `/predict` | 72hr AI forecast |
| GET | `/report/national` | Full NDMA situation report |
| GET | `/workers` | All workers + status |
| GET | `/stats` | Dashboard summary stats |
