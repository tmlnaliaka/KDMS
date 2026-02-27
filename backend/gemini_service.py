"""
gemini_service.py — All Gemini 1.5 Flash API calls for KDMS (4 jobs).
"""
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

_client = None

def _get_client():
    global _client
    if _client is None:
        if not GEMINI_KEY or GEMINI_KEY.startswith("AIza..."):
            return None
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        _client = genai.GenerativeModel("gemini-1.5-flash")
    return _client


def _extract_json(text: str):
    """Strip markdown fences and parse JSON."""
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    return json.loads(text)


async def score_county_risk(county: str, weather: dict) -> dict:
    """
    Job 1 — Risk Scoring.
    Returns: {risk_score: 0-100, disaster_type, confidence, reasoning}
    """
    model = _get_client()
    if not model:
        return _mock_risk(county, weather)

    prompt = f"""You are a disaster risk analyst for Kenya's NDMA.
Analyse this weather data for {county} county and output a JSON risk assessment.

Weather data:
{json.dumps(weather, indent=2)}

Respond with ONLY valid JSON (no markdown):
{{
  "risk_score": <integer 0-100>,
  "disaster_type": "<Flood|Drought|Wildfire|Earthquake|Landslide|None>",
  "confidence": "<High|Medium|Low>",
  "reasoning": "<one sentence explanation>"
}}"""
    try:
        resp = model.generate_content(prompt)
        return _extract_json(resp.text)
    except Exception as e:
        print(f"[Gemini] Risk scoring error: {e}")
        return _mock_risk(county, weather)


def _mock_risk(county: str, weather: dict) -> dict:
    import random
    rainfall = weather.get("rainfall_mm", 0)
    score = min(100, int(rainfall * 2 + random.randint(0, 30)))
    dtype = "Flood" if rainfall > 20 else "Drought" if rainfall < 2 else "None"
    return {
        "risk_score":   score,
        "disaster_type": dtype,
        "confidence":   "Low",
        "reasoning":    f"Mock analysis — rainfall {rainfall:.1f}mm detected in {county}.",
    }


async def generate_72hr_prediction(county_forecasts: list[dict]) -> list[dict]:
    """
    Job 2 — 72hr Predictive Warning.
    Returns: [{county, threat, probability, estimated_time, recommended_action}]
    """
    model = _get_client()
    if not model:
        return _mock_predictions(county_forecasts)

    prompt = f"""You are a disaster prediction AI for Kenya's National Disaster Management Authority.
Analyse the following 7-day weather forecasts for multiple Kenya counties and identify which are 
likely to experience a disaster in the next 72 hours.

Forecasts:
{json.dumps(county_forecasts[:15], indent=2)}

Respond with ONLY a valid JSON array (no markdown) of counties at risk:
[
  {{
    "county": "<county name>",
    "threat": "<Flood|Drought|Wildfire|Landslide|Storm>",
    "probability": "<High|Medium|Low>",
    "estimated_time": "<within 24hrs|within 48hrs|within 72hrs>",
    "recommended_action": "<brief NDMA action>"
  }}
]
Return an empty array [] if no threats identified."""
    try:
        resp = model.generate_content(prompt)
        return _extract_json(resp.text)
    except Exception as e:
        print(f"[Gemini] Prediction error: {e}")
        return _mock_predictions(county_forecasts)


def _mock_predictions(forecasts: list) -> list:
    return [
        {
            "county":             "Tana River",
            "threat":             "Flood",
            "probability":        "High",
            "estimated_time":     "within 24hrs",
            "recommended_action": "Pre-position boats and deploy rescue teams",
        },
        {
            "county":             "Turkana",
            "threat":             "Drought",
            "probability":        "High",
            "estimated_time":     "within 72hrs",
            "recommended_action": "Activate water trucking and food aid distribution",
        },
    ]


async def generate_sms_alert(disaster: dict, refuges: list[dict]) -> dict:
    """
    Job 3 — SMS Alert (English + Swahili, <160 chars each).
    Returns: {english, swahili}
    """
    model = _get_client()
    if not model:
        return _mock_sms(disaster)

    refuge_list = ", ".join([r["name"] for r in refuges[:3]])
    prompt = f"""You are writing emergency community SMS alerts for disaster-affected Kenyans.

Disaster details:
- Type: {disaster.get('type')}
- Location: {disaster.get('location')} county
- Severity: {disaster.get('severity')}
- People affected: {disaster.get('affected_people', 0)}
- Refuge sites: {refuge_list or 'Nearest county offices'}

Write TWO SMS alerts — one in English, one in Swahili — each UNDER 160 characters.
Include: disaster type, refuge location, action to take.
Respond with ONLY valid JSON (no markdown):
{{"english": "<message>", "swahili": "<message>"}}"""
    try:
        resp = model.generate_content(prompt)
        return _extract_json(resp.text)
    except Exception as e:
        print(f"[Gemini] SMS error: {e}")
        return _mock_sms(disaster)


def _mock_sms(disaster: dict) -> dict:
    county = disaster.get("location", "your area")
    dtype  = disaster.get("type", "disaster")
    return {
        "english": f"NDMA ALERT: {dtype} in {county}. Move to nearest refuge site immediately. Stay safe. Call 1199 for help.",
        "swahili": f"TAHADHARI NDMA: {dtype} katika {county}. Nenda kituo cha wakimbizi. Piga simu 1199 kwa msaada.",
    }


async def generate_national_report(disasters: list[dict], stats: dict) -> str:
    """
    Job 4 — National Situation Report for NDMA officers.
    Returns: formatted markdown string.
    """
    model = _get_client()
    if not model:
        return _mock_report(disasters, stats)

    active = [d for d in disasters if d.get("status") == "active"]
    prompt = f"""You are the National Disaster Management Authority (NDMA) Kenya AI system.
Generate a professional Situation Report (SitRep) for senior NDMA officers.

Current situation:
- Active disasters: {stats.get('active_disasters', len(active))}
- Total affected people: {stats.get('total_affected', 0):,}
- Counties at high risk: {stats.get('high_risk_counties', 0)}
- Workers deployed: {stats.get('deployed_workers', 0)}

Active disasters:
{json.dumps(active[:10], indent=2)}

Write a professional markdown SitRep with sections:
1. Executive Summary
2. Active Incidents (table)
3. Resource Status
4. Immediate Actions Required
5. 72-Hour Outlook

Use ## for section headers. Be concise and professional."""
    try:
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        print(f"[Gemini] Report error: {e}")
        return _mock_report(disasters, stats)


def _mock_report(disasters: list, stats: dict) -> str:
    active_count = stats.get("active_disasters", len([d for d in disasters if d.get("status") == "active"]))
    return f"""## NDMA Kenya — National Situation Report
*Generated: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*

## Executive Summary
There are currently **{active_count} active disasters** across Kenya counties.
Total estimated affected population: **{stats.get('total_affected', 0):,} people**.

## Active Incidents
| County | Type | Severity | Affected |
|--------|------|----------|----------|
""" + "\n".join(
    f"| {d.get('county_name','—')} | {d.get('type','—')} | {d.get('severity','—')} | {d.get('affected_people',0):,} |"
    for d in disasters[:8] if d.get("status") == "active"
) + """

## Immediate Actions Required
- Dispatch additional search-and-rescue teams to high-severity zones
- Activate water trucking for drought-affected northern counties
- Coordinate with Kenya Red Cross for medical supply replenishment

## 72-Hour Outlook
Continued monitoring of Tana River basin for flooding due to upstream rainfall.
*(This is a demonstration report — connect Gemini API for live analysis)*"""
