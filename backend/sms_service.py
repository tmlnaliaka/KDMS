"""
sms_service.py — Africa's Talking SMS integration for KDMS.
Uses sandbox mode by default (no real SMS sent, no cost).
"""
import os
from dotenv import load_dotenv

load_dotenv()

AT_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
AT_API_KEY  = os.getenv("AFRICASTALKING_API_KEY", "")


def _get_sms_client():
    if not AT_API_KEY:
        return None
    try:
        import africastalking
        africastalking.initialize(AT_USERNAME, AT_API_KEY)
        return africastalking.SMS
    except Exception as e:
        print(f"[SMS] Init error: {e}")
        return None


async def send_bulk_sms(phone_numbers: list[str], message: str) -> dict:
    """
    Send bulk SMS via Africa's Talking.
    Returns: {sent: int, failed: int, sandbox: bool}
    """
    if not phone_numbers:
        return {"sent": 0, "failed": 0, "sandbox": True, "error": "No recipients"}

    # Ensure numbers are in E.164 format (+254...)
    formatted = []
    for num in phone_numbers:
        n = num.strip().replace(" ", "")
        if n.startswith("07") or n.startswith("01"):
            n = "+254" + n[1:]
        elif n.startswith("254") and not n.startswith("+"):
            n = "+" + n
        formatted.append(n)

    sms = _get_sms_client()
    if not sms:
        print(f"[SMS] MOCK — Would send to {len(formatted)} numbers: {message[:60]}...")
        return {"sent": len(formatted), "failed": 0, "sandbox": True, "mock": True}

    try:
        resp = sms.send(message, formatted, sender_id="NDMA-KE")
        sent   = sum(1 for r in resp.get("SMSMessageData", {}).get("Recipients", []) if r.get("status") == "Success")
        failed = len(formatted) - sent
        return {
            "sent":    sent,
            "failed":  failed,
            "sandbox": AT_USERNAME == "sandbox",
        }
    except Exception as e:
        print(f"[SMS] Send error: {e}")
        return {"sent": 0, "failed": len(formatted), "error": str(e)}
