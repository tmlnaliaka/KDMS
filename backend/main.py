"""
main.py — FastAPI backend for KDMS (Kenya Disaster Management System)
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from database import (
    init_db, get_all_counties, get_all_disasters, insert_disaster,
    get_all_workers, dispatch_worker, insert_alert, get_alerts,
    get_refuges_for_county, fetchone, fetchall, execute, update_county_risk
)
from gemini_service import (
    generate_72hr_prediction, generate_sms_alert, generate_national_report, get_admin_chat_response
)
from sms_service import send_bulk_sms
from data_sources import fetch_forecast


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        from scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[Main] Scheduler warning: {e}")
    yield
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="KDMS API",
    description="Kenya Disaster Management System — powered by Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ────────────────────────────────────────────────────────────

class DisasterReport(BaseModel):
    type: str
    severity: str = "Medium"
    county_id: Optional[int] = None
    location: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    affected_people: int = 0
    description: str


class DispatchRequest(BaseModel):
    worker_id: int
    disaster_id: int


class AlertRequest(BaseModel):
    disaster_id: int
    county_id: Optional[int] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "system": "KDMS — Kenya Disaster Management System",
        "version": "1.0.0",
        "status": "operational",
        "powered_by": "Gemini 1.5 Flash",
    }


@app.get("/disasters")
async def get_disasters(status: Optional[str] = None):
    """All active or past disasters. Filter with ?status=active or ?status=resolved."""
    return await get_all_disasters(status)


@app.get("/disasters/{disaster_id}")
async def get_disaster(disaster_id: int):
    row = await fetchone(
        "SELECT d.*, c.name as county_name FROM disasters d "
        "LEFT JOIN counties c ON d.county_id=c.id WHERE d.id=?",
        (disaster_id,)
    )
    if not row:
        raise HTTPException(404, "Disaster not found")
    return row


@app.post("/report")
async def submit_report(report: DisasterReport):
    """Field worker submits a disaster report."""
    disaster_id = await insert_disaster({
        "type":            report.type,
        "severity":        report.severity,
        "county_id":       report.county_id,
        "location":        report.location,
        "lat":             report.lat,
        "lng":             report.lng,
        "affected_people": report.affected_people,
        "description":     report.description,
        "source":          "field_worker",
        "status":          "active",
    })
    return {"success": True, "disaster_id": disaster_id, "message": "Report submitted successfully"}


@app.get("/counties/risk")
async def get_county_risks():
    """All 47 counties with their current risk scores."""
    counties = await get_all_counties()
    return counties


@app.get("/counties/{county_id}")
async def get_county(county_id: int):
    row = await fetchone("SELECT * FROM counties WHERE id=?", (county_id,))
    if not row:
        raise HTTPException(404, "County not found")
    disasters = await get_all_disasters()
    county_disasters = [d for d in disasters if d.get("county_id") == county_id]
    refuges = await get_refuges_for_county(county_id)
    return {"county": row, "disasters": county_disasters, "refuges": refuges}


@app.get("/workers")
async def get_workers():
    """All field workers with their current status and location."""
    return await get_all_workers()


@app.post("/dispatch")
async def dispatch(req: DispatchRequest):
    """Assign a field worker to a disaster."""
    worker = await fetchone("SELECT * FROM workers WHERE id=?", (req.worker_id,))
    if not worker:
        raise HTTPException(404, "Worker not found")
    disaster = await fetchone("SELECT * FROM disasters WHERE id=?", (req.disaster_id,))
    if not disaster:
        raise HTTPException(404, "Disaster not found")
    await dispatch_worker(req.worker_id, req.disaster_id)
    return {
        "success": True,
        "message": f"{worker['name']} dispatched to {disaster['location']}",
        "worker_id": req.worker_id,
        "disaster_id": req.disaster_id,
    }


@app.post("/alert/send")
async def send_alert(req: AlertRequest, background_tasks: BackgroundTasks):
    """Generate AI SMS alert and send to county workers/community via Africa's Talking."""
    disaster = await fetchone(
        "SELECT d.*, c.name as county_name FROM disasters d "
        "LEFT JOIN counties c ON d.county_id=c.id WHERE d.id=?",
        (req.disaster_id,)
    )
    if not disaster:
        raise HTTPException(404, "Disaster not found")

    county_id = req.county_id or disaster.get("county_id")
    refuges   = await get_refuges_for_county(county_id) if county_id else []

    # Generate AI SMS text
    sms_text  = await generate_sms_alert(disaster, refuges)

    # Get worker phones in the affected county
    workers   = await fetchall("SELECT phone FROM workers WHERE county_id=?", (county_id,))
    phones    = [w["phone"] for w in workers if w.get("phone")]

    async def _send(phones, message):
        result = await send_bulk_sms(phones, message)
        if phones:
            await insert_alert(req.disaster_id, sms_text["english"], sms_text["swahili"], result["sent"])

    background_tasks.add_task(_send, phones, sms_text["english"])

    return {
        "success":       True,
        "message_en":    sms_text["english"],
        "message_sw":    sms_text["swahili"],
        "recipients":    len(phones),
        "disaster_id":   req.disaster_id,
    }


@app.get("/alerts")
async def list_alerts():
    return await get_alerts()


@app.get("/predict")
async def predict():
    """72-hour AI disaster prediction for all Kenya counties (Gemini)."""
    counties = await get_all_counties()
    forecasts = []
    for county in counties[:20]:  # limit API calls
        fc = await fetch_forecast(county["lat"], county["lng"])
        if fc:
            forecasts.append({
                "county": county["name"],
                "region": county.get("region"),
                "forecast": fc.get("daily", {}),
            })
    predictions = await generate_72hr_prediction(forecasts)
    return {"predictions": predictions, "generated_at": datetime.utcnow().isoformat()}


@app.get("/report/national")
async def national_report():
    """Full AI-generated NDMA situation report (Gemini)."""
    disasters = await get_all_disasters()
    active    = [d for d in disasters if d.get("status") == "active"]
    workers   = await get_all_workers()
    counties  = await get_all_counties()

    stats = {
        "active_disasters":  len(active),
        "total_affected":    sum(d.get("affected_people", 0) for d in active),
        "high_risk_counties": len([c for c in counties if c.get("risk_score", 0) >= 70]),
        "deployed_workers":  len([w for w in workers if w.get("status") == "deployed"]),
        "available_workers": len([w for w in workers if w.get("status") == "available"]),
    }

    report = await generate_national_report(disasters, stats)
    return {
        "report":       report,
        "stats":        stats,
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.patch("/disasters/{disaster_id}/resolve")
async def resolve_disaster(disaster_id: int):
    """Mark a disaster as resolved."""
    await execute(
        "UPDATE disasters SET status='resolved', resolved_at=datetime('now') WHERE id=?",
        (disaster_id,)
    )
    return {"success": True, "disaster_id": disaster_id}

class ChatMessage(BaseModel):
    role: str
    content: str
class ChatRequest(BaseModel):
    messages: list[ChatMessage]

@app.post("/api/chat")
async def admin_chat(req: ChatRequest):
    """Gemini-powered chatbot for system administrators."""
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    
    # Gather some basic system context to inject
    stats = await get_stats()
    reply = await get_admin_chat_response(msgs, stats)
    return {"reply": reply}

@app.get("/api/warnings")
async def early_warnings():
    """Returns predictive early warnings with precise timelines."""
    # Reutilizes the 72hr prediction engine which incorporates weather API data
    pred = await predict()
    
    # Format predictions specifically for the UI warnings ticker
    warnings = []
    for p in pred.get("predictions", []):
        if p.get("probability") in ["High", "Medium"]:
            warnings.append({
                "id": f"warn_{p['county']}_{p['threat']}",
                "county": p["county"],
                "threat": p["threat"],
                "timeline": p["estimated_time"],
                "severity": p["probability"],
                "action": p["recommended_action"]
            })
            
    return {"warnings": warnings, "timestamp": datetime.utcnow().isoformat()}

@app.get("/stats")
async def get_stats():
    """Quick summary stats for the dashboard header."""
    disasters = await get_all_disasters()
    workers   = await get_all_workers()
    counties  = await get_all_counties()
    active    = [d for d in disasters if d.get("status") == "active"]
    return {
        "active_disasters":   len(active),
        "total_disasters":    len(disasters),
        "total_affected":     sum(d.get("affected_people", 0) for d in active),
        "deployed_workers":   len([w for w in workers if w.get("status") == "deployed"]),
        "available_workers":  len([w for w in workers if w.get("status") == "available"]),
        "high_risk_counties": len([c for c in counties if c.get("risk_score", 0) >= 70]),
        "counties_monitored": len(counties),
    }
