"""
scheduler.py — APScheduler background job that runs every 30 min.
Pulls data from all external APIs, updates county risk scores via Gemini.
"""
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from database import (
    get_all_counties, update_county_risk, insert_disaster, fetchall
)
from data_sources import fetch_weather, fetch_earthquakes, fetch_wildfires
from gemini_service import score_county_risk

_scheduler = BackgroundScheduler(timezone="Africa/Nairobi")


def _run_async(coro):
    """Helper to run async functions from sync APScheduler context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _collect_and_analyse():
    print(f"\n[Scheduler] ⏰ Data collection started — {datetime.now().strftime('%H:%M:%S')}")

    # 1. Fetch + score each county
    counties = await get_all_counties()
    print(f"[Scheduler] Processing {len(counties)} counties...")

    for county in counties[:10]:  # First 10 to respect free-tier rate limits
        weather = await fetch_weather(county["name"], county["lat"], county["lng"])
        risk    = await score_county_risk(county["name"], weather)
        await update_county_risk(county["id"], risk.get("risk_score", 0))

    # 2. Fetch earthquakes → auto-insert new disasters
    quakes = await fetch_earthquakes()
    for q in quakes[:5]:
        # Only insert high/medium magnitude quakes not already recorded
        if q["magnitude"] >= 3.5:
            existing = await fetchall(
                "SELECT id FROM disasters WHERE type='Earthquake' AND lat=? AND lng=?",
                (round(q["lat"], 2), round(q["lng"], 2))
            )
            if not existing:
                await insert_disaster({
                    "type":            "Earthquake",
                    "severity":        q["severity"],
                    "location":        q.get("place", "East Africa"),
                    "lat":             q["lat"],
                    "lng":             q["lng"],
                    "affected_people": 0,
                    "description":     f"M{q['magnitude']} earthquake at depth {q['depth_km']}km — {q['place']}",
                    "source":          "usgs",
                    "status":          "active",
                })

    # 3. Fetch wildfires → auto-insert if significant
    fires = await fetch_wildfires()
    if fires:
        print(f"[Scheduler] {len(fires)} wildfire hotspots detected")
        # Group by proximity — simple check, insert one cluster entry
        if len(fires) > 5:
            fire = fires[0]
            existing = await fetchall(
                "SELECT id FROM disasters WHERE type='Wildfire' AND lat BETWEEN ? AND ?",
                (fire["lat"] - 0.5, fire["lat"] + 0.5)
            )
            if not existing:
                await insert_disaster({
                    "type":            "Wildfire",
                    "severity":        "High" if len(fires) > 20 else "Medium",
                    "location":        "Northern Kenya",
                    "lat":             fire["lat"],
                    "lng":             fire["lng"],
                    "affected_people": 0,
                    "description":     f"{len(fires)} active fire hotspots detected via NASA FIRMS satellite.",
                    "source":          "nasa_firms",
                    "status":          "active",
                })

    print(f"[Scheduler] ✅ Cycle complete — {datetime.now().strftime('%H:%M:%S')}\n")


def _job():
    _run_async(_collect_and_analyse())


def start_scheduler():
    _scheduler.add_job(
        _job,
        trigger=IntervalTrigger(minutes=30),
        id="data_collection",
        name="KDMS Data Collection",
        replace_existing=True,
    )
    _scheduler.start()
    print("[Scheduler] ✅ Background scheduler started (every 30 min)")
    # Run immediately on startup
    _job()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()
        print("[Scheduler] Stopped")
